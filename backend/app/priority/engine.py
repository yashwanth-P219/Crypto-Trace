from typing import List, Dict, Any, Optional
from app.database.models import AddressLabel, EntityType

class PriorityCalculationEngine:
    """
    Computes an explainable 0–100 investigation priority score indicating
    how urgently an investigator should examine a specific lead (wallet, path, or transaction).
    Explicitly separates 'behavioral risk' from 'investigation urgency'.
    """

    @staticmethod
    def calculate_wallet_priority(
        wallet_address: str,
        risk_score: Optional[float] = None,
        patterns: List[Any] = None,
        hops_from_source: int = 1,
        total_volume_eth: float = 0.0,
        entity_type: str = "UNKNOWN",
        entity_name: Optional[str] = None,
        is_source: bool = False
    ) -> Dict[str, Any]:
        points = 0.0
        reasons: List[str] = []
        evidence: List[str] = []
        patterns = patterns or []
        hops_from_source = hops_from_source if hops_from_source is not None else 1
        total_volume_eth = total_volume_eth if total_volume_eth is not None else 0.0

        # 1. Behavioral Risk Score (up to 30 points)
        if risk_score is not None and risk_score > 0:
            risk_contribution = min(30.0, (risk_score / 100.0) * 30.0)
            points += risk_contribution
            if risk_score >= 60:
                reasons.append(f"Elevated behavioral risk score ({risk_score:.0f}/100) warrants urgent scrutiny")

        # 2. Severe Patterns Detected (up to 25 points)
        pattern_pts = 0.0
        for p in patterns:
            p_name = getattr(p, "pattern_name", None) or (p.get("pattern_name") if isinstance(p, dict) else str(p))
            p_sev = getattr(p, "severity", None) or (p.get("severity") if isinstance(p, dict) else "MEDIUM")
            tx_hashes = getattr(p, "related_transaction_hashes", None) or (p.get("related_transaction_hashes") if isinstance(p, dict) else [])

            if str(p_sev).upper() == "CRITICAL":
                pattern_pts += 15.0
                reasons.append(f"Critical topological pattern detected: {p_name}")
            elif str(p_sev).upper() == "HIGH":
                pattern_pts += 10.0
                reasons.append(f"High-severity pattern detected: {p_name}")
            else:
                pattern_pts += 5.0

            if tx_hashes:
                evidence.extend(tx_hashes[:3])

        points += min(25.0, pattern_pts)

        # 3. Known Exchange / VASP Liquidation Gateway (up to 25 points)
        norm_entity = (entity_type or "UNKNOWN").upper()
        if norm_entity in ("EXCHANGE", "VASP"):
            points += 25.0
            reasons.append(f"Identified cashout gateway into verified VASP/Exchange: {entity_name or 'Known VASP'}")
        elif norm_entity in ("MIXER", "SCAM", "SCAM_ASSOCIATED"):
            points += 25.0
            reasons.append(f"Direct connection to obfuscation service: {entity_name or 'Illicit Entity'}")
        elif norm_entity == "BRIDGE":
            points += 20.0
            reasons.append(f"Cross-chain bridge flight point: {entity_name or 'Bridge Service'}")
        elif norm_entity == "DEX":
            points += 15.0
            reasons.append(f"Decentralized exchange conversion point: {entity_name or 'DEX Router'}")

        # 4. Proximity to Source/Victim (up to 20 points)
        if hops_from_source == 1:
            points += 20.0
            reasons.append("Direct 1st-hop counterparty to suspect/victim wallet")
        elif hops_from_source == 2:
            points += 12.0
            reasons.append("2nd-hop intermediary distribution hub")
        elif hops_from_source == 3:
            points += 7.0
            reasons.append("3rd-hop downstream transit wallet")

        # 5. Volume Throughput (up to 15 points)
        if total_volume_eth >= 10.0:
            points += 15.0
            reasons.append(f"Very high value throughput ({total_volume_eth:.2f} ETH)")
        elif total_volume_eth >= 2.0:
            points += 10.0
            reasons.append(f"Significant fund volume ({total_volume_eth:.2f} ETH)")
        elif total_volume_eth >= 0.5:
            points += 5.0

        # Bound score strictly between 0 and 100
        final_score = max(0.0, min(100.0, points))

        # Categorize
        if final_score >= 75.0:
            category = "CRITICAL"
        elif final_score >= 50.0:
            category = "HIGH"
        elif final_score >= 25.0:
            category = "MEDIUM"
        else:
            category = "LOW"

        if not reasons:
            reasons.append("Standard monitoring profile with baseline activity")

        # Deduplicate evidence
        clean_evidence = list(dict.fromkeys(evidence))

        return {
            "priority_score": round(final_score, 1),
            "priority_category": category,
            "reasons": reasons,
            "supporting_evidence": clean_evidence
        }
