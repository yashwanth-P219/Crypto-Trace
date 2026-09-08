from typing import List, Dict, Any, Optional
from app.database.models import AddressLabel, EntityType

class InvestigationPriorityEngine:
    @staticmethod
    def rank_wallets(
        wallets_data: List[Dict[str, Any]],
        labels_map: Dict[str, AddressLabel],
        source_address: str
    ) -> List[Dict[str, Any]]:
        """
        Ranks candidate investigation wallets using multi-criteria forensic priority scoring.
        """
        scored_wallets = []

        for w in wallets_data:
            addr = w.get("address", "")
            norm_addr = addr.lower()
            if norm_addr == source_address.lower():
                continue # source is already known suspect

            label_entry = labels_map.get(norm_addr)
            entity_type = label_entry.entity_type.value if label_entry else w.get("entity_type", "UNKNOWN")
            entity_name = label_entry.entity_name if label_entry else w.get("label", "Unknown Address")

            in_val = float(w.get("total_incoming", 0.0))
            out_val = float(w.get("total_outgoing", 0.0))
            hops = int(w.get("hops_from_source", 999))
            risk_score = float(w.get("risk_score", 0.0))

            priority_points = 0.0
            reasons = []

            # 1. Known VASP liquidation point
            if entity_type in ("VASP", "EXCHANGE"):
                priority_points += 40.0
                reasons.append(f"Immediate liquidation exit into verified exchange ({entity_name})")

            # 2. Mixer or sanctioned entity
            if entity_type in ("MIXER", "SCAM"):
                priority_points += 50.0
                reasons.append(f"Direct connection to flagged illicit entity: {entity_name}")

            # 3. High volume throughput
            if in_val >= 2.0 or out_val >= 2.0:
                priority_points += 20.0
                reasons.append(f"High value throughput: {max(in_val, out_val):.2f} ETH")

            # 4. Proximity to victim funds
            if hops == 1:
                priority_points += 25.0
                reasons.append("Direct 1-hop counterparty to suspect wallet")
            elif hops == 2:
                priority_points += 15.0
                reasons.append("Secondary 2-hop intermediary hub")
            elif hops == 3:
                priority_points += 10.0
                reasons.append("3-hop transit node")

            # 5. High risk score
            if risk_score >= 70:
                priority_points += 20.0
                reasons.append(f"High behavioral risk score ({risk_score:.0f}/100)")

            # 6. Bridge interaction
            if entity_type == "BRIDGE":
                priority_points += 30.0
                reasons.append(f"Cross-chain exit gateway ({entity_name})")

            priority_level = "LOW"
            if priority_points >= 60:
                priority_level = "CRITICAL"
            elif priority_points >= 40:
                priority_level = "HIGH"
            elif priority_points >= 20:
                priority_level = "MEDIUM"

            scored_wallets.append({
                "address": addr,
                "label": entity_name,
                "entity_type": entity_type,
                "hops_from_source": hops,
                "total_incoming": in_val,
                "total_outgoing": out_val,
                "priority_score": round(priority_points, 1),
                "priority_level": priority_level,
                "reasons": reasons,
                "action_recommendation": (
                    f"Freeze request / subpoena to {entity_name}"
                    if entity_type in ("VASP", "EXCHANGE")
                    else "Subpoena KYC records & trace outgoing hops"
                    if priority_level in ("CRITICAL", "HIGH")
                    else "Monitor for secondary activity"
                )
            })

        # Sort by priority_score descending
        scored_wallets.sort(key=lambda x: x["priority_score"], reverse=True)

        # Assign rank 1, 2, 3...
        for idx, item in enumerate(scored_wallets):
            item["priority_rank"] = idx + 1

        return scored_wallets
