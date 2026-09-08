import datetime
import statistics
from typing import List, Dict, Any, Set, Optional
from app.database.models import Transaction, AddressLabel, EntityType

def _get_tx_timestamp(tx: Any) -> Optional[datetime.datetime]:
    if hasattr(tx, 'block_timestamp') and tx.block_timestamp:
        return tx.block_timestamp
    if hasattr(tx, 'timestamp') and tx.timestamp:
        return tx.timestamp
    return None

def _get_tx_value(tx: Any) -> float:
    if hasattr(tx, 'value_eth') and tx.value_eth is not None:
        return float(tx.value_eth)
    if hasattr(tx, 'amount_native') and tx.amount_native is not None:
        return float(tx.amount_native)
    return 0.0

def _get_tx_from(tx: Any) -> str:
    return getattr(tx, 'from_address', '').lower()

def _get_tx_to(tx: Any) -> str:
    return (getattr(tx, 'to_address', '') or '').lower()


class FeatureExtractor:
    @staticmethod
    def extract_wallet_features(
        wallet_address: str,
        transactions: List[Any],
        labels_map: Optional[Dict[str, Any]] = None,
        hop_count: int = 1,
        patterns_list: Optional[List[Any]] = None,
        cycles_count: int = 0
    ) -> Dict[str, float]:
        """
        Extracts explainable numerical features for a single wallet from its transactions and graph context.
        Supports both Phase 1 and Phase 6 feature sets.
        """
        labels = labels_map or {}
        norm_wallet = wallet_address.lower()

        incoming = [tx for tx in transactions if _get_tx_to(tx) == norm_wallet]
        outgoing = [tx for tx in transactions if _get_tx_from(tx) == norm_wallet]

        incoming_vals = [_get_tx_value(tx) for tx in incoming]
        outgoing_vals = [_get_tx_value(tx) for tx in outgoing]
        all_vals = incoming_vals + outgoing_vals

        incoming_val = sum(incoming_vals)
        outgoing_val = sum(outgoing_vals)
        tx_count = len(incoming) + len(outgoing)

        counterparties: Set[str] = set()
        incoming_cps: Set[str] = set()
        outgoing_cps: Set[str] = set()

        for tx in incoming:
            frm = _get_tx_from(tx)
            if frm:
                counterparties.add(frm)
                incoming_cps.add(frm)
        for tx in outgoing:
            to_addr = _get_tx_to(tx)
            if to_addr:
                counterparties.add(to_addr)
                outgoing_cps.add(to_addr)

        unique_counterparties = len(counterparties)

        # Statistical metrics
        avg_val = statistics.mean(all_vals) if all_vals else 0.0
        med_val = statistics.median(all_vals) if all_vals else 0.0
        max_val = max(all_vals) if all_vals else 0.0

        # Duration & Frequency
        timestamps = [_get_tx_timestamp(tx) for tx in (incoming + outgoing) if _get_tx_timestamp(tx)]
        duration_hours = 0.0
        tx_freq = 0.0
        burst_score = 0.0

        if timestamps:
            timestamps.sort()
            duration_secs = max(1.0, (timestamps[-1] - timestamps[0]).total_seconds())
            duration_hours = max(0.1, duration_secs / 3600.0)
            tx_freq = tx_count / duration_hours
            if duration_secs < 1800 and tx_count >= 5:
                burst_score = 1.0
            elif tx_freq > 10.0:
                burst_score = 0.8

        # Rapid movement count
        rapid_count = 0
        if incoming and outgoing:
            for in_tx in incoming:
                in_t = _get_tx_timestamp(in_tx)
                if not in_t:
                    continue
                for out_tx in outgoing:
                    out_t = _get_tx_timestamp(out_tx)
                    if out_t and 0 <= (out_t - in_t).total_seconds() <= 900:
                        rapid_count += 1
                        break

        # Patterns counts
        p_list = patterns_list or []
        pattern_ids = [getattr(p, 'pattern_id', '') or getattr(p, 'finding_type', '') for p in p_list]
        rapid_transfer_count = float(rapid_count or pattern_ids.count("PAT-RAPID-TRANSFER") or pattern_ids.count("RAPID_MOVEMENT"))
        fund_split_count = float(pattern_ids.count("PAT-FUND-SPLITTING") or pattern_ids.count("FUND_SPLITTING"))
        consolidation_count = float(pattern_ids.count("PAT-FUND-CONSOLIDATION") or pattern_ids.count("FUND_CONSOLIDATION"))
        multi_hop_count = float(pattern_ids.count("PAT-MULTI-HOP") or pattern_ids.count("MULTI_HOP_DEPTH") or (1 if hop_count >= 3 else 0))
        cycle_count = float(cycles_count or pattern_ids.count("PAT-CIRCULAR-FLOW") or pattern_ids.count("CIRCULAR_MOVEMENT"))
        unusual_large_transfer_count = float(pattern_ids.count("PAT-SUDDEN-LARGE-TRANSFER") or pattern_ids.count("SUDDEN_LARGE_TRANSFER"))

        # Entity interactions
        known_entity_interaction = 0.0
        exchange_interaction = 0.0
        bridge_interaction = 0.0
        dex_interaction = 0.0
        high_risk_connections = 0.0

        for cp in counterparties:
            lbl = labels.get(cp)
            if lbl:
                etype = getattr(lbl, 'entity_type', None)
                etype_str = etype.value if hasattr(etype, 'value') else str(etype)
                if etype_str not in ("UNKNOWN", "PERSONAL_WALLET"):
                    known_entity_interaction = 1.0
                if etype_str in ("EXCHANGE", "VASP"):
                    exchange_interaction += 1.0
                elif etype_str == "BRIDGE":
                    bridge_interaction += 1.0
                elif etype_str == "DEX":
                    dex_interaction += 1.0
                elif etype_str in ("MIXER", "SCAM", "SCAM_ASSOCIATED"):
                    high_risk_connections += 1.0

        # Phase 1 compatibility scores
        fund_splitting_score = min(1.0, len(outgoing) / 5.0) if len(incoming) >= 1 and len(outgoing) >= 3 else 0.0
        fund_concentration_score = min(1.0, len(incoming) / 5.0) if len(incoming) >= 3 and len(outgoing) <= 2 else 0.0
        rapid_movement_indicator = 1.0 if rapid_count > 0 else 0.0
        cross_chain_indicator = 1.0 if bridge_interaction > 0 else 0.0

        return {
            # Core Phase 6 23 features
            "transaction_count": float(tx_count),
            "incoming_transaction_count": float(len(incoming)),
            "outgoing_transaction_count": float(len(outgoing)),
            "unique_counterparties": float(unique_counterparties),
            "total_incoming_value": float(incoming_val),
            "total_outgoing_value": float(outgoing_val),
            "average_transaction_value": float(round(avg_val, 4)),
            "median_transaction_value": float(round(med_val, 4)),
            "maximum_transaction_value": float(round(max_val, 4)),
            "transaction_frequency": float(round(tx_freq, 4)),
            "burst_activity_score": float(burst_score),
            "rapid_transfer_count": rapid_transfer_count,
            "fund_split_count": fund_split_count,
            "consolidation_count": consolidation_count,
            "multi_hop_count": multi_hop_count,
            "cycle_count": cycle_count,
            "unusual_large_transfer_count": unusual_large_transfer_count,
            "known_entity_interaction": known_entity_interaction,
            "exchange_interaction": float(exchange_interaction),
            "bridge_interaction": float(bridge_interaction),
            "DEX_interaction": float(dex_interaction),
            "suspicious_pattern_count": float(len(p_list)),
            "path_depth": float(hop_count),

            # Backward-compatible Phase 1 aliases
            "incoming_value": float(incoming_val),
            "outgoing_value": float(outgoing_val),
            "wallet_activity_duration": float(duration_hours),
            "hop_count": float(hop_count),
            "fund_splitting_score": float(fund_splitting_score),
            "fund_concentration_score": float(fund_concentration_score),
            "high_risk_connections": float(high_risk_connections),
            "cross_chain_indicator": float(cross_chain_indicator),
            "rapid_movement_indicator": float(rapid_movement_indicator)
        }
