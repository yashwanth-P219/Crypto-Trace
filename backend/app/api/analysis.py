import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Case, Transaction, AddressLabel, RiskFinding, User, FindingSeverity
from app.api.auth import get_current_user
from app.graph.graph_builder import GraphBuilder
from app.graph.path_analysis import PathAnalyzer
from app.risk.rules import SuspiciousPatternEngine
from app.risk.priority import InvestigationPriorityEngine
from app.risk.explainability import RiskExplainability

logger = logging.getLogger("api.analysis")
router = APIRouter(prefix="/analysis", tags=["Graph & Trail Analysis"])

def get_case_extended_transactions(db: Session, case_id: str, suspect_wallet: Optional[str] = None, max_hops: int = 5) -> List[Transaction]:
    all_tx_ids = set()
    result_txs = []
    visited_addresses = set()
    current_frontier = set()

    if suspect_wallet:
        root = suspect_wallet.lower().strip()
        visited_addresses.add(root)
        current_frontier.add(root)

    # 1. Transactions directly assigned to this case
    case_txs = db.query(Transaction).filter(Transaction.case_id == case_id).all()
    for tx in case_txs:
        if tx.id not in all_tx_ids:
            all_tx_ids.add(tx.id)
            result_txs.append(tx)
            if tx.to_address:
                visited_addresses.add(tx.to_address.lower())
            if tx.from_address:
                visited_addresses.add(tx.from_address.lower())

    # If no transactions exist for suspect_wallet yet, auto-sync from Sepolia
    if not result_txs and suspect_wallet:
        try:
            from app.services.transaction_service import TransactionService
            logger.info(f"Auto-syncing real on-chain transactions for {suspect_wallet}...")
            TransactionService.sync_wallet_transactions(db, suspect_wallet, case_id=case_id)
            synced_txs = db.query(Transaction).filter(
                (Transaction.case_id == case_id) |
                (Transaction.from_address.ilike(suspect_wallet)) |
                (Transaction.to_address.ilike(suspect_wallet))
            ).all()
            for tx in synced_txs:
                if tx.id not in all_tx_ids:
                    all_tx_ids.add(tx.id)
                    result_txs.append(tx)
                    if tx.to_address:
                        visited_addresses.add(tx.to_address.lower())
                    if tx.from_address:
                        visited_addresses.add(tx.from_address.lower())
        except Exception as e:
            logger.warning(f"Auto-sync for {suspect_wallet} failed: {e}")

    if not suspect_wallet:
        return result_txs

    expanded_addresses = set()
    current_frontier = {suspect_wallet.lower().strip()}

    # Include destinations of case_txs in frontier
    for tx in case_txs:
        if tx.to_address:
            current_frontier.add(tx.to_address.lower())

    # 2. Multi-hop forward expansion from suspect wallet
    for _ in range(max_hops):
        to_expand = current_frontier - expanded_addresses
        if not to_expand:
            break
        expanded_addresses.update(to_expand)

        # For newly discovered frontier addresses, if not yet cached, attempt auto-sync from Sepolia
        for addr in list(to_expand):
            has_outgoing = db.query(Transaction).filter(Transaction.from_address.ilike(addr)).first()
            if not has_outgoing:
                try:
                    from app.services.transaction_service import TransactionService
                    TransactionService.sync_wallet_transactions(db, addr, case_id=case_id)
                except Exception:
                    pass

        outgoing = db.query(Transaction).filter(
            Transaction.from_address.in_(list(to_expand))
        ).all()

        next_frontier = set()
        for tx in outgoing:
            if tx.id not in all_tx_ids:
                all_tx_ids.add(tx.id)
                result_txs.append(tx)
            if tx.to_address:
                to_lower = tx.to_address.lower()
                if to_lower not in expanded_addresses:
                    next_frontier.add(to_lower)
        current_frontier = next_frontier

    # 3. Direct incoming transactions to suspect wallet
    incoming = db.query(Transaction).filter(
        Transaction.to_address.ilike(suspect_wallet)
    ).all()
    for tx in incoming:
        if tx.id not in all_tx_ids:
            all_tx_ids.add(tx.id)
            result_txs.append(tx)

    return result_txs

@router.get("/graph/{case_id}")
def get_case_graph(
    case_id: str,
    hops: int = Query(default=3, ge=1, le=5),
    suspicious_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    transactions = get_case_extended_transactions(db, case_id, case.suspect_wallet, max_hops=hops)
    labels_map = {lbl.address.lower(): lbl for lbl in db.query(AddressLabel).all()}

    # Gather suspicious transaction hashes
    findings = db.query(RiskFinding).filter(
        (RiskFinding.case_id == case_id) |
        (RiskFinding.wallet_address.ilike(case.suspect_wallet if case.suspect_wallet else ""))
    ).all()
    suspicious_txs = set()
    for f in findings:
        if f.evidence_txs:
            for h in f.evidence_txs:
                suspicious_txs.add(h)

    gb = GraphBuilder()
    gb.populate_from_transactions(transactions, labels_map)
    graph = gb.get_graph()

    pa = PathAnalyzer(graph)
    subgraph = pa.get_k_hop_subgraph(
        source=case.suspect_wallet,
        max_hops=hops,
        suspicious_only=suspicious_only,
        suspicious_tx_hashes=suspicious_txs
    )

    return subgraph

@router.get("/trail/{case_id}")
def get_money_trail(
    case_id: str,
    max_hops: int = Query(default=5, ge=1, le=5),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    transactions = get_case_extended_transactions(db, case_id, case.suspect_wallet, max_hops=max_hops)
    labels_map = {lbl.address.lower(): lbl for lbl in db.query(AddressLabel).all()}

    gb = GraphBuilder()
    gb.populate_from_transactions(transactions, labels_map)
    graph = gb.get_graph()

    pa = PathAnalyzer(graph)
    vasp_paths = pa.trace_paths_to_vasp(case.suspect_wallet, max_hops=max_hops)

    has_known_vasp = any("VASP" in p.get("destination_vasp", "") or "Exchange" in p.get("destination_vasp", "") or "Binance" in p.get("destination_vasp", "") for p in vasp_paths)

    if vasp_paths:
        if has_known_vasp:
            status_msg = f"Discovered {len(vasp_paths)} verified liquidation route(s) terminating at recognized VASP."
        else:
            status_msg = f"Discovered {len(vasp_paths)} forward liquidation trail(s) terminating at active destination sink wallet(s)."
    else:
        status_msg = "No verified liquidation path was found in the currently indexed data."

    return {
        "case_id": case_id,
        "victim_name": case.victim_name,
        "suspect_wallet": case.suspect_wallet,
        "amount_lost": case.amount_lost,
        "currency": case.currency,
        "paths_to_vasp": vasp_paths,
        "verified_paths_count": len(vasp_paths),
        "status_message": status_msg
    }

@router.get("/patterns/{case_id}")
def get_detected_patterns(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    wallet = case.suspect_wallet or ""
    findings = db.query(RiskFinding).filter(
        (RiskFinding.case_id == case_id) |
        (RiskFinding.wallet_address.ilike(wallet if wallet else ""))
    ).all()

    # If no findings in DB, dynamically evaluate patterns against case transactions
    if not findings and wallet:
        try:
            txs = get_case_extended_transactions(db, case_id, wallet, max_hops=4)
            if txs:
                labels_map = {lbl.address.lower(): lbl for lbl in db.query(AddressLabel).all()}
                gb = GraphBuilder()
                gb.populate_from_transactions(txs, labels_map)
                pa = PathAnalyzer(gb.get_graph())
                cycles = pa.find_cycles(wallet)

                evaluated = SuspiciousPatternEngine.evaluate_patterns(
                    wallet_address=wallet,
                    transactions=txs,
                    labels_map=labels_map,
                    max_hop_depth=min(4, max(1, len(txs))),
                    cycles_detected=cycles
                )
                for item in evaluated:
                    sev_str = item.get("severity")
                    if isinstance(sev_str, FindingSeverity):
                        sev_enum = sev_str
                    else:
                        try:
                            sev_enum = FindingSeverity(str(sev_str).upper())
                        except Exception:
                            sev_enum = FindingSeverity.MEDIUM

                    rf = RiskFinding(
                        case_id=case_id,
                        wallet_address=wallet,
                        finding_type=item.get("finding_type", "SUSPICIOUS_ACTIVITY"),
                        severity=sev_enum,
                        score_delta=float(item.get("score_delta", 15.0)),
                        evidence_txs=item.get("evidence_txs", []),
                        explanation=item.get("explanation", "")
                    )
                    db.add(rf)
                db.commit()
                findings = db.query(RiskFinding).filter(RiskFinding.case_id == case_id).all()
        except Exception as e:
            logger.error(f"Error evaluating patterns dynamically for case {case_id}: {e}")
            db.rollback()

    findings_dicts = [
        {
            "finding_type": f.finding_type,
            "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            "score_delta": f.score_delta,
            "explanation": f.explanation,
            "evidence_txs": f.evidence_txs or []
        }
        for f in findings
    ]
    risk_summary = RiskExplainability.compute_risk_score(findings_dicts)
    return {
        "case_id": case_id,
        "risk_assessment": risk_summary,
        "findings": [
            {
                "id": f.id,
                "finding_type": f.finding_type,
                "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                "score_delta": f.score_delta,
                "explanation": f.explanation,
                "evidence_txs": f.evidence_txs or [],
                "created_at": str(f.created_at) if f.created_at else None
            }
            for f in findings
        ]
    }
