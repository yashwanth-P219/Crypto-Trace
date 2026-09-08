import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database.models import Transaction, Case, AddressLabel, AnalysisPattern
from app.analysis.pattern_models import PatternFinding, PatternAnalysisResponse, CasePatternsResponse
from app.analysis.pattern_detector import PatternDetector
from app.graph.graph_service import GraphService
from app.graph.path_analysis import PathAnalyzer

class PatternService:
    @staticmethod
    def analyze_wallet_patterns(
        db: Session,
        wallet_address: str,
        case_id: Optional[str] = None,
        max_hops: int = 3,
        blockchain: str = "Ethereum",
        chain_id: int = 11155111,
        persist: bool = True
    ) -> PatternAnalysisResponse:
        norm_wallet = wallet_address.lower()

        # 1. Fetch transactions involving the target wallet
        transactions = []
        if case_id:
            transactions = db.query(Transaction).filter(
                Transaction.case_id == case_id,
                (Transaction.from_address.ilike(norm_wallet)) |
                (Transaction.to_address.ilike(norm_wallet))
            ).all()

        if not transactions:
            transactions = db.query(Transaction).filter(
                (Transaction.from_address.ilike(norm_wallet)) |
                (Transaction.to_address.ilike(norm_wallet))
            ).all()

        # 2. Build multi-hop graph to extract paths and cycles
        from app.graph.graph_builder import GraphBuilder
        graph_res = GraphService.build_wallet_graph(
            db=db,
            wallet_address=norm_wallet,
            max_hops=max_hops,
            direction="both"
        )

        builder = GraphBuilder()
        builder.populate_from_transactions(
            transactions=graph_res.edges,
            root_wallet=norm_wallet,
            node_hops={n.address: n.hops_from_root for n in graph_res.nodes}
        )
        nx_graph = builder.get_graph()

        # 3. Discover flow paths using PathAnalyzer
        pa = PathAnalyzer(nx_graph)
        paths = pa.discover_money_flow_paths(norm_wallet, max_hops=max_hops, direction="outgoing")
        if not paths:
            paths = pa.discover_money_flow_paths(norm_wallet, max_hops=max_hops, direction="both")

        # 4. Check if any path terminal reaches a known labeled entity
        known_entity_reached = False
        entity_name = None

        all_path_nodes = set()
        for p in paths:
            all_path_nodes.update(p)

        if all_path_nodes:
            labeled = db.query(AddressLabel).filter(
                AddressLabel.address.in_([a.lower() for a in all_path_nodes])
            ).all()
            for lbl in labeled:
                if lbl.address.lower() != norm_wallet and lbl.entity_type.value not in ("UNKNOWN", "PERSONAL_WALLET"):
                    known_entity_reached = True
                    entity_name = f"{lbl.entity_name} ({lbl.entity_type.value})"
                    break

        # 5. Execute pattern analysis
        findings = PatternDetector.analyze_wallet(
            wallet_address=norm_wallet,
            transactions=transactions,
            networkx_graph=nx_graph,
            graph_paths=paths,
            max_hop_depth=max_hops,
            known_entity_reached=known_entity_reached,
            entity_name=entity_name
        )

        # 6. Optionally persist findings to analysis_patterns table
        if persist and findings:
            try:
                # Remove prior patterns for this wallet/case to avoid duplication
                db.query(AnalysisPattern).filter(
                    AnalysisPattern.wallet_address.ilike(norm_wallet),
                    AnalysisPattern.case_id == case_id
                ).delete(synchronize_session=False)

                for f in findings:
                    rec = AnalysisPattern(
                        case_id=case_id,
                        wallet_address=norm_wallet,
                        blockchain=blockchain,
                        chain_id=chain_id,
                        pattern_id=f.pattern_id,
                        pattern_name=f.pattern_name,
                        severity=f.severity,
                        confidence=f.confidence,
                        description=f.description,
                        related_wallets=f.related_wallets,
                        related_transaction_hashes=f.related_transaction_hashes,
                        evidence_json=f.evidence,
                        detected_at=f.detected_at,
                        created_at=datetime.datetime.utcnow()
                    )
                    db.add(rec)
                db.commit()
            except Exception:
                db.rollback()

        # 7. Summary metrics
        severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for f in findings:
            sev = f.severity.upper()
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        summary = {
            "transactions_analyzed": len(transactions),
            "max_hops_evaluated": max_hops,
            "patterns_count": len(findings),
            "severity_breakdown": severity_counts,
            "known_entity_destination_identified": known_entity_reached
        }

        return PatternAnalysisResponse(
            wallet_address=norm_wallet,
            blockchain=blockchain,
            chain_id=chain_id,
            case_id=case_id,
            total_patterns_detected=len(findings),
            patterns=findings,
            summary=summary,
            analyzed_at=datetime.datetime.utcnow()
        )

    @staticmethod
    def analyze_case_patterns(db: Session, case_id: str, max_hops: int = 3) -> CasePatternsResponse:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise ValueError(f"Case with ID '{case_id}' not found.")

        wallet_res = PatternService.analyze_wallet_patterns(
            db=db,
            wallet_address=case.suspect_wallet,
            case_id=case_id,
            max_hops=max_hops,
            blockchain=case.blockchain or "Ethereum",
            persist=True
        )

        return CasePatternsResponse(
            case_id=case_id,
            suspect_wallet=case.suspect_wallet,
            blockchain=case.blockchain or "Ethereum",
            total_patterns_detected=wallet_res.total_patterns_detected,
            patterns=wallet_res.patterns,
            analyzed_at=wallet_res.analyzed_at
        )
