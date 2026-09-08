import datetime
import statistics
import networkx as nx
from typing import List, Dict, Any, Optional, Set
from app.analysis.pattern_models import PatternFinding
from app.analysis import config

def _get_tx_timestamp(tx: Any) -> Optional[datetime.datetime]:
    if hasattr(tx, 'block_timestamp') and tx.block_timestamp:
        return tx.block_timestamp
    if hasattr(tx, 'timestamp') and tx.timestamp:
        return tx.timestamp
    return None

def _get_tx_hash(tx: Any) -> str:
    if hasattr(tx, 'tx_hash') and tx.tx_hash:
        return tx.tx_hash
    if hasattr(tx, 'transaction_hash') and tx.transaction_hash:
        return tx.transaction_hash
    return ""

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


class PatternRules:
    """
    Modular forensic rules for detecting behavioral transaction patterns.
    Strictly applies neutral investigative terminology without declaring criminality.
    """

    @staticmethod
    def detect_rapid_transfers(wallet_address: str, transactions: List[Any]) -> List[PatternFinding]:
        findings = []
        norm_wallet = wallet_address.lower()
        incoming = [tx for tx in transactions if _get_tx_to(tx) == norm_wallet and _get_tx_timestamp(tx)]
        outgoing = [tx for tx in transactions if _get_tx_from(tx) == norm_wallet and _get_tx_timestamp(tx)]

        if not incoming or not outgoing:
            return findings

        # Check pairs of incoming and subsequent outgoing transfers
        for in_tx in incoming:
            in_time = _get_tx_timestamp(in_tx)
            in_val = _get_tx_value(in_tx)
            in_hash = _get_tx_hash(in_tx)

            for out_tx in outgoing:
                out_time = _get_tx_timestamp(out_tx)
                out_hash = _get_tx_hash(out_tx)
                if in_hash == out_hash:
                    continue

                diff_seconds = (out_time - in_time).total_seconds()
                if 0 <= diff_seconds <= config.RAPID_TRANSFER_SECONDS:
                    out_val = _get_tx_value(out_tx)
                    findings.append(PatternFinding(
                        pattern_id="PAT-RAPID-TRANSFER",
                        pattern_name="Rapid Fund Transfer",
                        severity="HIGH" if diff_seconds < 300 else "MEDIUM",
                        confidence=0.88,
                        description=(
                            f"Inbound transfer of {in_val:.4f} ETH was followed by an outbound "
                            f"transfer of {out_val:.4f} ETH within {int(diff_seconds)} seconds."
                        ),
                        wallet_address=wallet_address,
                        related_wallets=[_get_tx_from(in_tx), _get_tx_to(out_tx)],
                        related_transaction_hashes=[in_hash, out_hash],
                        evidence={
                            "incoming_tx": in_hash,
                            "outgoing_tx": out_hash,
                            "time_difference_seconds": diff_seconds,
                            "incoming_amount_eth": in_val,
                            "outgoing_amount_eth": out_val,
                            "threshold_seconds": config.RAPID_TRANSFER_SECONDS
                        }
                    ))
                    return findings  # Return primary occurrence to avoid explosion
        return findings

    @staticmethod
    def detect_fund_splitting(wallet_address: str, transactions: List[Any]) -> List[PatternFinding]:
        findings = []
        norm_wallet = wallet_address.lower()
        incoming = [tx for tx in transactions if _get_tx_to(tx) == norm_wallet]
        outgoing = [tx for tx in transactions if _get_tx_from(tx) == norm_wallet]

        if not incoming or len(outgoing) < config.FUND_SPLIT_MIN_DESTINATIONS:
            return findings

        # Group outgoing by unique recipient addresses
        recipients = list(set(_get_tx_to(tx) for tx in outgoing if _get_tx_to(tx)))
        if len(recipients) >= config.FUND_SPLIT_MIN_DESTINATIONS:
            total_in = sum(_get_tx_value(tx) for tx in incoming)
            total_out = sum(_get_tx_value(tx) for tx in outgoing)
            out_hashes = [_get_tx_hash(tx) for tx in outgoing[:6]]
            in_hashes = [_get_tx_hash(tx) for tx in incoming[:2]]

            findings.append(PatternFinding(
                pattern_id="PAT-FUND-SPLITTING",
                pattern_name="Fund Splitting / Fan-Out",
                severity="HIGH",
                confidence=0.85,
                description=(
                    f"Funds received by the wallet were distributed into {len(recipients)} distinct "
                    f"destination wallets across {len(outgoing)} outbound transactions."
                ),
                wallet_address=wallet_address,
                related_wallets=recipients[:10],
                related_transaction_hashes=in_hashes + out_hashes,
                evidence={
                    "incoming_transaction_count": len(incoming),
                    "outgoing_transaction_count": len(outgoing),
                    "unique_destinations": len(recipients),
                    "total_incoming_value_eth": round(total_in, 4),
                    "total_outgoing_value_eth": round(total_out, 4),
                    "split_ratio": round(total_out / max(0.0001, total_in), 2)
                }
            ))
        return findings

    @staticmethod
    def detect_fund_consolidation(wallet_address: str, transactions: List[Any]) -> List[PatternFinding]:
        findings = []
        norm_wallet = wallet_address.lower()
        incoming = [tx for tx in transactions if _get_tx_to(tx) == norm_wallet]
        outgoing = [tx for tx in transactions if _get_tx_from(tx) == norm_wallet]

        if len(incoming) < config.FUND_CONSOLIDATION_MIN_SOURCES or not outgoing:
            return findings

        sources = list(set(_get_tx_from(tx) for tx in incoming if _get_tx_from(tx)))
        if len(sources) >= config.FUND_CONSOLIDATION_MIN_SOURCES and len(outgoing) <= 2:
            total_in = sum(_get_tx_value(tx) for tx in incoming)
            total_out = sum(_get_tx_value(tx) for tx in outgoing)
            in_hashes = [_get_tx_hash(tx) for tx in incoming[:6]]
            out_hashes = [_get_tx_hash(tx) for tx in outgoing]

            findings.append(PatternFinding(
                pattern_id="PAT-FUND-CONSOLIDATION",
                pattern_name="Fund Consolidation / Fan-In",
                severity="MEDIUM",
                confidence=0.80,
                description=(
                    f"Multiple inbound deposits ({len(sources)} source addresses, {total_in:.4f} ETH) "
                    f"were aggregated and consolidated into {len(outgoing)} outbound transfer(s)."
                ),
                wallet_address=wallet_address,
                related_wallets=sources[:10] + [_get_tx_to(tx) for tx in outgoing],
                related_transaction_hashes=in_hashes + out_hashes,
                evidence={
                    "incoming_sources_count": len(sources),
                    "incoming_transactions_count": len(incoming),
                    "consolidated_outgoing_count": len(outgoing),
                    "total_consolidated_eth": round(total_out, 4)
                }
            ))
        return findings

    @staticmethod
    def detect_multi_hop_movement(
        wallet_address: str,
        graph_paths: Optional[List[List[str]]] = None,
        max_hop_depth: int = 1
    ) -> List[PatternFinding]:
        findings = []
        deep_paths = []
        if graph_paths:
            deep_paths = [p for p in graph_paths if len(p) >= 4]  # 4 nodes = 3 hops

        if deep_paths or max_hop_depth >= 3:
            effective_depth = max(len(p) - 1 for p in deep_paths) if deep_paths else max_hop_depth
            path_sample = deep_paths[0] if deep_paths else [wallet_address]

            findings.append(PatternFinding(
                pattern_id="PAT-MULTI-HOP",
                pattern_name="Extended Multi-Hop Movement",
                severity="HIGH" if effective_depth >= 4 else "MEDIUM",
                confidence=0.85,
                description=(
                    f"Fund transfer flow traces through {effective_depth} sequential intermediary wallet hops, "
                    "distancing downstream funds from the origin address."
                ),
                wallet_address=wallet_address,
                related_wallets=path_sample[:8],
                related_transaction_hashes=[],
                evidence={
                    "max_hop_depth": effective_depth,
                    "sample_path": path_sample,
                    "total_deep_paths": len(deep_paths)
                }
            ))
        return findings

    @staticmethod
    def detect_high_frequency_burst(wallet_address: str, transactions: List[Any]) -> List[PatternFinding]:
        findings = []
        if len(transactions) < 5:
            return findings

        timestamps = sorted([_get_tx_timestamp(tx) for tx in transactions if _get_tx_timestamp(tx)])
        if len(timestamps) >= 5:
            span_seconds = max(1.0, (timestamps[-1] - timestamps[0]).total_seconds())
            span_minutes = span_seconds / 60.0
            tx_per_minute = len(transactions) / span_minutes

            if tx_per_minute >= config.BURST_TX_PER_MINUTE_THRESHOLD or (
                len(transactions) >= config.HIGH_FREQUENCY_TRANSACTION_COUNT and span_minutes <= config.HIGH_FREQUENCY_WINDOW_MINUTES
            ):
                findings.append(PatternFinding(
                    pattern_id="PAT-HIGH-FREQUENCY-BURST",
                    pattern_name="High-Frequency Burst Activity",
                    severity="MEDIUM",
                    confidence=0.82,
                    description=(
                        f"Anomalous transaction frequency detected: {len(transactions)} transactions executed "
                        f"within {int(span_minutes)} minutes ({tx_per_minute:.2f} tx/min)."
                    ),
                    wallet_address=wallet_address,
                    related_wallets=[],
                    related_transaction_hashes=[_get_tx_hash(tx) for tx in transactions[:5]],
                    evidence={
                        "transaction_count": len(transactions),
                        "window_minutes": round(span_minutes, 2),
                        "rate_per_minute": round(tx_per_minute, 2),
                        "threshold_per_minute": config.BURST_TX_PER_MINUTE_THRESHOLD
                    }
                ))
        return findings

    @staticmethod
    def detect_circular_movement(
        wallet_address: str,
        networkx_graph: Optional[nx.MultiDiGraph] = None
    ) -> List[PatternFinding]:
        findings = []
        if not networkx_graph or networkx_graph.number_of_nodes() < 2:
            return findings

        norm_wallet = wallet_address.lower()
        matched_node = None
        for n in networkx_graph.nodes():
            if str(n).lower() == norm_wallet:
                matched_node = n
                break

        if not matched_node:
            return findings

        try:
            # Look for simple cycles involving target wallet
            cycles = list(nx.simple_cycles(networkx_graph))
            target_cycles = [c for c in cycles if matched_node in c and len(c) <= config.CYCLE_DETECTION_MAX_LENGTH]
            if target_cycles:
                cycle = target_cycles[0]
                cycle_addrs = [str(x) for x in cycle]
                findings.append(PatternFinding(
                    pattern_id="PAT-CIRCULAR-FLOW",
                    pattern_name="Circular Fund Movement Loop",
                    severity="HIGH",
                    confidence=0.89,
                    description=(
                        f"Closed circular transaction loop detected containing {len(cycle)} wallets, "
                        "where fund flows cycle back to an originating or affiliated address."
                    ),
                    wallet_address=wallet_address,
                    related_wallets=cycle_addrs,
                    related_transaction_hashes=[],
                    evidence={
                        "cycle_length": len(cycle),
                        "cycle_addresses": cycle_addrs,
                        "total_cycles_detected": len(target_cycles)
                    }
                ))
        except Exception:
            pass

        return findings

    @staticmethod
    def detect_sudden_large_transfer(wallet_address: str, transactions: List[Any]) -> List[PatternFinding]:
        findings = []
        if len(transactions) < 3:
            return findings

        values = [_get_tx_value(tx) for tx in transactions]
        mean_val = statistics.mean(values)
        median_val = statistics.median(values)
        max_val = max(values)

        threshold = max(config.LARGE_TRANSFER_MIN_ETH, median_val * config.LARGE_TRANSFER_MULTIPLIER)

        if max_val >= threshold and max_val >= config.LARGE_TRANSFER_MIN_ETH:
            large_txs = [tx for tx in transactions if _get_tx_value(tx) == max_val]
            large_hash = _get_tx_hash(large_txs[0]) if large_txs else ""
            other_addr = _get_tx_to(large_txs[0]) if _get_tx_from(large_txs[0]) == wallet_address.lower() else _get_tx_from(large_txs[0])

            findings.append(PatternFinding(
                pattern_id="PAT-SUDDEN-LARGE-TRANSFER",
                pattern_name="Sudden Outlier Value Transfer",
                severity="MEDIUM",
                confidence=0.84,
                description=(
                    f"Outlier transfer of {max_val:.4f} ETH identified, exceeding the wallet's historical "
                    f"median transfer ({median_val:.4f} ETH) by a factor of {round(max_val / max(0.001, median_val), 1)}x."
                ),
                wallet_address=wallet_address,
                related_wallets=[other_addr] if other_addr else [],
                related_transaction_hashes=[large_hash] if large_hash else [],
                evidence={
                    "outlier_amount_eth": round(max_val, 4),
                    "historical_mean_eth": round(mean_val, 4),
                    "historical_median_eth": round(median_val, 4),
                    "deviation_factor": round(max_val / max(0.001, median_val), 2),
                    "threshold_applied_eth": round(threshold, 4)
                }
            ))
        return findings

    @staticmethod
    def detect_unusual_counterparty_behavior(wallet_address: str, transactions: List[Any]) -> List[PatternFinding]:
        findings = []
        norm_wallet = wallet_address.lower()

        incoming_cps = set(_get_tx_from(tx) for tx in transactions if _get_tx_to(tx) == norm_wallet and _get_tx_from(tx))
        outgoing_cps = set(_get_tx_to(tx) for tx in transactions if _get_tx_from(tx) == norm_wallet and _get_tx_to(tx))
        all_cps = incoming_cps.union(outgoing_cps)

        if len(all_cps) >= config.UNUSUAL_COUNTERPARTY_COUNT:
            findings.append(PatternFinding(
                pattern_id="PAT-UNUSUAL-COUNTERPARTY-SPREAD",
                pattern_name="Broad Counterparty Dispersion",
                severity="MEDIUM",
                confidence=0.80,
                description=(
                    f"Elevated counterparty diversity: wallet interacted directly with {len(all_cps)} unique "
                    f"counterparty addresses ({len(incoming_cps)} incoming, {len(outgoing_cps)} outgoing)."
                ),
                wallet_address=wallet_address,
                related_wallets=list(all_cps)[:10],
                related_transaction_hashes=[_get_tx_hash(tx) for tx in transactions[:4]],
                evidence={
                    "unique_counterparties_total": len(all_cps),
                    "incoming_counterparties": len(incoming_cps),
                    "outgoing_counterparties": len(outgoing_cps),
                    "threshold_applied": config.UNUSUAL_COUNTERPARTY_COUNT
                }
            ))
        return findings

    @staticmethod
    def detect_structurally_suspicious_paths(
        wallet_address: str,
        sub_findings: List[PatternFinding],
        known_entity_reached: bool = False,
        entity_name: Optional[str] = None
    ) -> List[PatternFinding]:
        findings = []
        finding_types = set(f.pattern_id for f in sub_findings)

        # Compound triggers: Multi-hop + (Rapid or Splitting or Consolidation or Known VASP exit)
        is_compound = (
            "PAT-MULTI-HOP" in finding_types and (
                "PAT-RAPID-TRANSFER" in finding_types or
                "PAT-FUND-SPLITTING" in finding_types or
                known_entity_reached
            )
        )

        if is_compound:
            contributing = [f.pattern_name for f in sub_findings]
            if known_entity_reached:
                contributing.append(f"Known Entity Gateway ({entity_name or 'VASP/Exchange'})")

            findings.append(PatternFinding(
                pattern_id="PAT-STRUCTURAL-MONEY-TRAIL",
                pattern_name="Structurally Compound Money Trail",
                severity="CRITICAL" if known_entity_reached else "HIGH",
                confidence=0.91,
                description=(
                    "Multi-layered behavioral path discovered combining extended multi-hop movement with "
                    f"{', '.join(contributing[:3])}."
                ),
                wallet_address=wallet_address,
                related_wallets=[],
                related_transaction_hashes=[],
                evidence={
                    "contributing_patterns": contributing,
                    "known_entity_reached": known_entity_reached,
                    "entity_name": entity_name
                }
            ))
        return findings
