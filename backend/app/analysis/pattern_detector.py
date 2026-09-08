import networkx as nx
from typing import List, Dict, Any, Optional
from app.analysis.pattern_models import PatternFinding
from app.analysis.pattern_rules import PatternRules

class PatternDetector:
    """
    Orchestrates modular forensic pattern detection rules.
    """

    @staticmethod
    def analyze_wallet(
        wallet_address: str,
        transactions: List[Any],
        networkx_graph: Optional[nx.MultiDiGraph] = None,
        graph_paths: Optional[List[List[str]]] = None,
        max_hop_depth: int = 1,
        known_entity_reached: bool = False,
        entity_name: Optional[str] = None
    ) -> List[PatternFinding]:
        if not transactions and not graph_paths and not networkx_graph:
            return []

        all_findings: List[PatternFinding] = []

        # 1. Rapid transfer detection
        all_findings.extend(PatternRules.detect_rapid_transfers(wallet_address, transactions))

        # 2. Fund splitting
        all_findings.extend(PatternRules.detect_fund_splitting(wallet_address, transactions))

        # 3. Fund consolidation
        all_findings.extend(PatternRules.detect_fund_consolidation(wallet_address, transactions))

        # 4. Multi-hop movement
        all_findings.extend(PatternRules.detect_multi_hop_movement(wallet_address, graph_paths, max_hop_depth))

        # 5. High frequency / burst activity
        all_findings.extend(PatternRules.detect_high_frequency_burst(wallet_address, transactions))

        # 6. Circular movement
        all_findings.extend(PatternRules.detect_circular_movement(wallet_address, networkx_graph))

        # 7. Sudden large transfer
        all_findings.extend(PatternRules.detect_sudden_large_transfer(wallet_address, transactions))

        # 8. Unusual counterparty behavior
        all_findings.extend(PatternRules.detect_unusual_counterparty_behavior(wallet_address, transactions))

        # 9. Structurally suspicious compound path
        compound_findings = PatternRules.detect_structurally_suspicious_paths(
            wallet_address,
            all_findings,
            known_entity_reached=known_entity_reached,
            entity_name=entity_name
        )
        all_findings.extend(compound_findings)

        return all_findings
