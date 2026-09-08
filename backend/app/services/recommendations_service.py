import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database.models import Case, Transaction, AnalysisPattern, RiskAssessmentRecord, Wallet
from app.database.schemas import InvestigationRecommendation, CaseRecommendationsResponse

class RecommendationsService:
    @staticmethod
    def generate_recommendations(db: Session, case_id: str) -> CaseRecommendationsResponse:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            return CaseRecommendationsResponse(
                case_id=case_id,
                total_recommendations=0,
                recommendations=[]
            )

        recommendations: List[InvestigationRecommendation] = []

        # 1. Check if suspect wallet or tx hash exists
        if not case.suspect_wallet and not case.transaction_hash:
            recommendations.append(InvestigationRecommendation(
                id=f"REC-{uuid.uuid4().hex[:6].upper()}",
                recommendation_type="EVIDENCE_ACQUISITION",
                title="Acquire Initial Blockchain Transaction Seed",
                description="Complainant has not yet provided a suspect wallet address or on-chain transaction hash.",
                priority="CRITICAL",
                reasoning=[
                    "Blockchain analytics requires a valid on-chain seed to construct money trails and graph topologies.",
                    "Victim reported incident without raw cryptographic hashes."
                ],
                suggested_action="Request victim's exchange withdrawal receipt, transaction confirmation emails, or UPI/bank payment memo matching crypto purchase."
            ))
            return CaseRecommendationsResponse(
                case_id=case_id,
                total_recommendations=len(recommendations),
                recommendations=recommendations
            )

        # 2. Analyze case transactions
        txs = db.query(Transaction).filter(Transaction.case_id == case_id).all()
        suspect = (case.suspect_wallet or "").lower()

        # Outflows from suspect wallet
        outflows = [tx for tx in txs if tx.from_address and tx.from_address.lower() == suspect]
        if outflows:
            # Sort by largest value
            outflows_sorted = sorted(outflows, key=lambda x: x.value_eth or 0.0, reverse=True)
            largest = outflows_sorted[0]
            recommendations.append(InvestigationRecommendation(
                id=f"REC-{uuid.uuid4().hex[:6].upper()}",
                recommendation_type="PRIORITY_TARGET",
                title=f"Trace Primary Outflow Recipient: {largest.to_address[:10]}...",
                description=f"Direct recipient of {largest.value_eth:.4f} ETH from the primary suspect wallet.",
                priority="HIGH",
                target_address=largest.to_address,
                target_tx=largest.tx_hash,
                reasoning=[
                    f"Direct counterparty to suspect address {suspect[:10]}...",
                    f"Received significant volume ({largest.value_eth:.4f} ETH) in confirmed transaction {largest.tx_hash[:12]}..."
                ],
                suggested_action="Expand multi-hop graph exploration by 2 hops downstream from this wallet."
            ))

        # 3. Check detected patterns
        patterns = db.query(AnalysisPattern).filter(AnalysisPattern.case_id == case_id).all()
        pattern_types = {p.pattern_name for p in patterns}

        if any("SPLIT" in p for p in pattern_types) or any("RAPID" in p for p in pattern_types):
            recommendations.append(InvestigationRecommendation(
                id=f"REC-{uuid.uuid4().hex[:6].upper()}",
                recommendation_type="STRUCTURING_INTERCEPTION",
                title="Rapid Peeling / Structuring Interception",
                description="Suspicious layering pattern detected indicating automated splitting or rapid fund redirection.",
                priority="HIGH",
                reasoning=[
                    "Structuring patterns detected across multiple intermediary transit wallets.",
                    "Indicates deliberate obfuscation to defeat AML detection thresholds."
                ],
                suggested_action="Flag intermediary addresses for ongoing balance monitoring and alert triggers."
            ))

        # 4. Check known VASP and Exchange destinations
        if suspect:
            known_wallets = (
                db.query(Wallet)
                .filter(Wallet.entity_type.in_(["EXCHANGE", "VASP"]))
                .all()
            )
            for kw in known_wallets:
                # Check if suspect sent funds to this known entity
                direct_hit = any(
                    tx.to_address and tx.to_address.lower() == kw.address.lower()
                    for tx in outflows
                )
                if direct_hit:
                    recommendations.append(InvestigationRecommendation(
                        id=f"REC-{uuid.uuid4().hex[:6].upper()}",
                        recommendation_type="VASP_SUBPOENA",
                        title=f"Issue Subpoena to {kw.label or 'Regulated Exchange'}",
                        description=f"Victim funds reached verified {kw.label or 'Exchange'} deposit infrastructure at {kw.address[:10]}...",
                        priority="CRITICAL",
                        target_address=kw.address,
                        reasoning=[
                            f"Verified VASP/Exchange entity detected in destination money trail.",
                            "Regulated VASP holds KYC and withdrawal audit logs for this deposit."
                        ],
                        suggested_action=f"Generate Standardized Forensic Report and serve Section 91 CrPC notice to legal compliance desk of {kw.label or 'VASP'}."
                    ))

        # 5. General Evidence preservation recommendation
        recommendations.append(InvestigationRecommendation(
            id=f"REC-{uuid.uuid4().hex[:6].upper()}",
            recommendation_type="EVIDENCE_PRESERVATION",
            title="Preserve Cryptographic Blockchain Artifacts",
            description="Ensure all transaction receipts and graph visual snapshots are locked with SHA-256 integrity hashes.",
            priority="MEDIUM",
            reasoning=[
                "Evidence locker guarantees chain of custody for cyber courtroom presentation.",
                "Produces reproducible SHA-256 hashes verifying zero alteration."
            ],
            suggested_action="Verify evidence integrity hashes in the Evidence Locker and compile formal dossier."
        ))

        return CaseRecommendationsResponse(
            case_id=case_id,
            total_recommendations=len(recommendations),
            recommendations=recommendations
        )
