from typing import List, Dict, Any, Optional
from datetime import timedelta
from app.database.models import Transaction, AddressLabel, EntityType, FindingSeverity
from app.risk.schemas import RiskFactorContribution

# Configurable Risk Scoring Weights
FACTOR_WEIGHTS = {
    "RAPID_TRANSFER": 15.0,
    "FUND_SPLITTING": 20.0,
    "FUND_CONSOLIDATION": 10.0,
    "MULTI_HOP": 15.0,
    "HIGH_FREQUENCY_BURST": 10.0,
    "CIRCULAR_FLOW": 15.0,
    "SUDDEN_LARGE_TRANSFER": 10.0,
    "UNUSUAL_COUNTERPARTY": 10.0,
    "VASP_LIQUIDATION_EXIT": 15.0,
    "HIGH_RISK_COUNTERPARTY": 25.0,
    "STRUCTURAL_MONEY_TRAIL": 20.0,
}

class RuleBasedRiskScorer:
    """
    Transparent, deterministic rule-based scoring engine for investigation prioritization.
    Normalizes scores strictly to 0-100 with explainable factor contributions.
    """

    @staticmethod
    def calculate_score(
        findings: List[Any],
        features: Optional[Dict[str, float]] = None,
        base_score: float = 0.0
    ) -> Dict[str, Any]:
        total_points = base_score
        contributions: List[RiskFactorContribution] = []
        evidence_txs: List[str] = []
        patterns_detected: List[str] = []
        seen_factors = set()

        for f in findings:
            pid = getattr(f, 'pattern_id', '') or getattr(f, 'finding_type', '')
            pname = getattr(f, 'pattern_name', '') or str(pid)
            explanation = getattr(f, 'description', '') or getattr(f, 'explanation', '')
            ev_txs = getattr(f, 'related_transaction_hashes', []) or getattr(f, 'evidence_txs', [])
            wallets = getattr(f, 'related_wallets', [])

            evidence_txs.extend(ev_txs)
            patterns_detected.append(pname)

            # Map pattern to factor weight
            weight = 10.0
            if "RAPID" in pid:
                weight = FACTOR_WEIGHTS["RAPID_TRANSFER"]
                factor_key = "rapid_transfer"
            elif "SPLIT" in pid:
                weight = FACTOR_WEIGHTS["FUND_SPLITTING"]
                factor_key = "fund_splitting"
            elif "CONSOLIDATION" in pid:
                weight = FACTOR_WEIGHTS["FUND_CONSOLIDATION"]
                factor_key = "fund_consolidation"
            elif "MULTI-HOP" in pid or "MULTI_HOP" in pid:
                weight = FACTOR_WEIGHTS["MULTI_HOP"]
                factor_key = "multi_hop_movement"
            elif "FREQUENCY" in pid or "BURST" in pid:
                weight = FACTOR_WEIGHTS["HIGH_FREQUENCY_BURST"]
                factor_key = "high_frequency_burst"
            elif "CIRCULAR" in pid:
                weight = FACTOR_WEIGHTS["CIRCULAR_FLOW"]
                factor_key = "circular_movement"
            elif "LARGE" in pid:
                weight = FACTOR_WEIGHTS["SUDDEN_LARGE_TRANSFER"]
                factor_key = "sudden_large_transfer"
            elif "COUNTERPARTY" in pid:
                weight = FACTOR_WEIGHTS["UNUSUAL_COUNTERPARTY"]
                factor_key = "unusual_counterparty_behavior"
            elif "VASP" in pid or "EXCHANGE" in pid:
                weight = FACTOR_WEIGHTS["VASP_LIQUIDATION_EXIT"]
                factor_key = "vasp_interaction"
            elif "STRUCTURAL" in pid:
                weight = FACTOR_WEIGHTS["STRUCTURAL_MONEY_TRAIL"]
                factor_key = "structurally_compound_trail"
            elif "HIGH_RISK" in pid or "MIXER" in pid:
                weight = FACTOR_WEIGHTS["HIGH_RISK_COUNTERPARTY"]
                factor_key = "high_risk_counterparty"
            else:
                factor_key = pid.lower()
                weight = getattr(f, 'score_delta', 10.0)

            if factor_key not in seen_factors:
                seen_factors.add(factor_key)
                total_points += weight
                contributions.append(RiskFactorContribution(
                    factor=factor_key,
                    points=weight,
                    explanation=explanation,
                    supporting_transactions=ev_txs[:4],
                    supporting_wallets=wallets[:4]
                ))

        # Check features for additional factors if not already added
        if features:
            if features.get("high_risk_connections", 0.0) > 0 and "high_risk_counterparty" not in seen_factors:
                seen_factors.add("high_risk_counterparty")
                total_points += FACTOR_WEIGHTS["HIGH_RISK_COUNTERPARTY"]
                contributions.append(RiskFactorContribution(
                    factor="high_risk_counterparty",
                    points=FACTOR_WEIGHTS["HIGH_RISK_COUNTERPARTY"],
                    explanation="Observed direct connection with flagged high-risk mixer or scam-associated entity."
                ))
            if features.get("exchange_interaction", 0.0) > 0 and "vasp_interaction" not in seen_factors:
                seen_factors.add("vasp_interaction")
                total_points += FACTOR_WEIGHTS["VASP_LIQUIDATION_EXIT"]
                contributions.append(RiskFactorContribution(
                    factor="vasp_interaction",
                    points=FACTOR_WEIGHTS["VASP_LIQUIDATION_EXIT"],
                    explanation="Fund trail reaches a recognized exchange/VASP gateway custody address."
                ))

        # Strictly normalize score to 0 - 100
        final_score = min(100.0, max(0.0, round(total_points, 1)))

        # Categorize
        if final_score >= 75.0:
            category = "CRITICAL"
        elif final_score >= 50.0:
            category = "HIGH"
        elif final_score >= 25.0:
            category = "MEDIUM"
        else:
            category = "LOW"

        return {
            "risk_score": final_score,
            "risk_category": category,
            "rule_based_score": final_score,
            "contributions": contributions,
            "patterns_detected": list(set(patterns_detected)),
            "evidence_txs": list(set(evidence_txs))
        }


class SuspiciousPatternEngine:
    """
    Backward-compatible pattern engine for Phase 1 unit tests.
    """
    @staticmethod
    def evaluate_patterns(
        wallet_address: str,
        transactions: List[Transaction],
        labels_map: Dict[str, AddressLabel],
        max_hop_depth: int = 1,
        cycles_detected: Optional[List[List[str]]] = None
    ) -> List[Dict[str, Any]]:
        findings = []
        norm_wallet = wallet_address.lower()

        incoming = [tx for tx in transactions if tx.to_address.lower() == norm_wallet]
        outgoing = [tx for tx in transactions if tx.from_address.lower() == norm_wallet]

        # 1. Rapid Movement: Funds dispersed within 15 minutes of receipt
        if incoming and outgoing:
            for in_tx in incoming:
                rapid_outgoings = [
                    out_tx for out_tx in outgoing
                    if out_tx.timestamp and in_tx.timestamp
                    and 0 <= (out_tx.timestamp - in_tx.timestamp).total_seconds() <= 900
                ]
                if rapid_outgoings:
                    findings.append({
                        "finding_type": "RAPID_MOVEMENT",
                        "severity": FindingSeverity.HIGH,
                        "score_delta": 15.0,
                        "evidence_txs": [in_tx.transaction_hash] + [t.transaction_hash for t in rapid_outgoings[:3]],
                        "explanation": (
                            f"Funds ({in_tx.amount_native:.4f} ETH) were moved to downstream counterparties "
                            f"within {int((rapid_outgoings[0].timestamp - in_tx.timestamp).total_seconds() / 60)} minutes of receipt."
                        )
                    })
                    break

        # 2. Fund Splitting
        if incoming and len(outgoing) >= 3:
            total_out_split = sum(t.amount_native for t in outgoing)
            findings.append({
                "finding_type": "FUND_SPLITTING",
                "severity": FindingSeverity.HIGH,
                "score_delta": 15.0,
                "evidence_txs": [t.transaction_hash for t in outgoing[:4]],
                "explanation": (
                    f"Layering pattern detected: incoming funds were split and routed into "
                    f"{len(outgoing)} separate destination addresses (total outgoing: {total_out_split:.4f} ETH)."
                )
            })

        # 3. Fund Consolidation
        if len(incoming) >= 3 and len(outgoing) == 1:
            findings.append({
                "finding_type": "FUND_CONSOLIDATION",
                "severity": FindingSeverity.MEDIUM,
                "score_delta": 10.0,
                "evidence_txs": [t.transaction_hash for t in incoming[:3]] + [outgoing[0].transaction_hash],
                "explanation": (
                    f"Consolidation pattern detected: {len(incoming)} smaller deposits were combined "
                    f"into a single outgoing transfer of {outgoing[0].amount_native:.4f} ETH."
                )
            })

        # 4. Multi-Hop Laundering Depth (depth >= 3)
        if max_hop_depth >= 3:
            findings.append({
                "finding_type": "MULTI_HOP_DEPTH",
                "severity": FindingSeverity.HIGH,
                "score_delta": 15.0,
                "evidence_txs": [tx.transaction_hash for tx in transactions[:3]],
                "explanation": (
                    f"Multi-hop fund laundering trail detected across {max_hop_depth} hops "
                    "designed to obscure the direct connection to the victim deposit."
                )
            })

        # 5. High Transaction Frequency / Burst Activity
        if len(transactions) >= 10:
            ts_list = sorted([tx.timestamp for tx in transactions if tx.timestamp])
            if ts_list:
                span_minutes = max(1.0, (ts_list[-1] - ts_list[0]).total_seconds() / 60.0)
                if len(transactions) / span_minutes >= 0.5:
                    findings.append({
                        "finding_type": "UNUSUAL_TRANSACTION_BURST",
                        "severity": FindingSeverity.MEDIUM,
                        "score_delta": 10.0,
                        "evidence_txs": [t.transaction_hash for t in transactions[:3]],
                        "explanation": (
                            f"Burst activity detected: {len(transactions)} transactions executed "
                            f"within {int(span_minutes)} minutes."
                        )
                    })

        # 6. High-Risk Counterparties (Mixers, Scams)
        flagged_counterparties = []
        for tx in (incoming + outgoing):
            other = tx.to_address.lower() if tx.from_address.lower() == norm_wallet else tx.from_address.lower()
            lbl = labels_map.get(other)
            if lbl and lbl.entity_type in (EntityType.MIXER, EntityType.SCAM, EntityType.SCAM_ASSOCIATED):
                flagged_counterparties.append((other, lbl, tx.transaction_hash))

        if flagged_counterparties:
            addr, lbl, tx_hash = flagged_counterparties[0]
            findings.append({
                "finding_type": "HIGH_RISK_COUNTERPARTY",
                "severity": FindingSeverity.CRITICAL,
                "score_delta": 20.0,
                "evidence_txs": [tx_hash],
                "explanation": (
                    f"Direct interaction observed with high-risk flagged entity: {lbl.entity_name} "
                    f"({lbl.entity_type.value}) at address {addr[:10]}...{addr[-6:]}."
                )
            })

        # 7. Circular Fund Movement
        if cycles_detected:
            findings.append({
                "finding_type": "CIRCULAR_MOVEMENT",
                "severity": FindingSeverity.HIGH,
                "score_delta": 10.0,
                "evidence_txs": [tx.transaction_hash for tx in transactions[:2]],
                "explanation": (
                    "Circular fund flow detected where assets cycled through intermediary "
                    "wallets and returned to an affiliated address (wash trading/layering loop)."
                )
            })

        # 8. Sudden Large Transfer
        large_txs = [tx for tx in transactions if tx.amount_native >= 2.0]
        if large_txs:
            findings.append({
                "finding_type": "SUDDEN_LARGE_TRANSFER",
                "severity": FindingSeverity.MEDIUM,
                "score_delta": 10.0,
                "evidence_txs": [large_txs[0].transaction_hash],
                "explanation": (
                    f"Abnormally high value transfer of {large_txs[0].amount_native:.4f} ETH "
                    "identified in the suspect flow."
                )
            })

        # 9. Cross-Chain Bridge Movement
        bridge_txs = []
        for tx in outgoing:
            lbl = labels_map.get(tx.to_address.lower())
            if lbl and lbl.entity_type == EntityType.BRIDGE:
                bridge_txs.append((tx, lbl))
        if bridge_txs:
            tx, lbl = bridge_txs[0]
            findings.append({
                "finding_type": "CROSS_CHAIN_MOVEMENT",
                "severity": FindingSeverity.MEDIUM,
                "score_delta": 10.0,
                "evidence_txs": [tx.transaction_hash],
                "explanation": (
                    f"Funds deposited into cross-chain bridge gateway ({lbl.entity_name}) "
                    "to exit the origin chain."
                )
            })

        # 10. Connection to Known VASP / Liquidation Exit
        vasp_exits = []
        for tx in outgoing:
            lbl = labels_map.get(tx.to_address.lower())
            if lbl and lbl.entity_type in (EntityType.VASP, EntityType.EXCHANGE):
                vasp_exits.append((tx, lbl))
        if vasp_exits:
            tx, lbl = vasp_exits[0]
            findings.append({
                "finding_type": "VASP_LIQUIDATION_EXIT",
                "severity": FindingSeverity.HIGH,
                "score_delta": 15.0,
                "evidence_txs": [tx.transaction_hash],
                "explanation": (
                    f"Direct liquidation transfer identified into verified VASP/Exchange custody: "
                    f"{lbl.entity_name} ({tx.amount_native:.4f} ETH)."
                )
            })

        return findings
