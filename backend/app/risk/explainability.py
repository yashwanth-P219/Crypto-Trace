from typing import List, Dict, Any, Optional
from app.risk.schemas import RiskFactorContribution

class RiskExplainability:
    @staticmethod
    def compute_risk_score(findings: List[Dict[str, Any]], base_score: float = 0.0) -> Dict[str, Any]:
        """
        Computes an explainable 0-100 Investigation Risk Score based on forensic rule findings.
        Preserves backward compatibility for Phase 1 demo tests.
        """
        total_score = base_score
        reasons = []

        for finding in findings:
            delta = float(finding.get("score_delta", 0.0))
            ftype = finding.get("finding_type")
            explanation = finding.get("explanation")
            evidence = finding.get("evidence_txs", [])

            total_score += delta
            reasons.append({
                "delta": delta,
                "type": ftype,
                "reason": explanation,
                "evidence_txs": evidence
            })

        # Cap score between 0 and 100
        score = min(100.0, max(0.0, round(total_score, 1)))

        # Determine Risk Level
        if score >= 75.0:
            level = "CRITICAL"
        elif score >= 50.0:
            level = "HIGH"
        elif score >= 25.0:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "score": score,
            "level": level,
            "title": "Investigation Risk Score",
            "reasons": reasons,
            "disclaimer": (
                "Analytical Prioritization Notice: This score reflects behavioral risk factors "
                "and does not constitute legal proof of guilt. All conclusions must be verified "
                "by an investigator using underlying blockchain transactions."
            )
        }

    @staticmethod
    def generate_why_this_risk(contributions: List[RiskFactorContribution], risk_category: str) -> List[str]:
        """
        Generates readable, transparent forensic justifications answering 'Why did this score increase?'.
        """
        lines = []
        if not contributions:
            return ["No anomalous behavioral patterns or risk factors were detected in the indexed transactions."]

        for c in contributions:
            lines.append(f"+{int(c.points)} pts [{c.factor.replace('_', ' ').title()}]: {c.explanation}")

        return lines
