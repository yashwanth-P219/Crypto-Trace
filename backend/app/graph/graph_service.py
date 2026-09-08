import re
import logging
from typing import Dict, Any, Optional, List, Set
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func

from app.database.models import Transaction, Case, AddressLabel
from app.graph.graph_builder import GraphBuilder
from app.graph.path_analysis import PathAnalyzer
from app.graph.graph_models import (
    GraphResponse,
    PathDiscoveryResponse,
    CounterpartiesResponse,
    CounterpartyDetail,
    GraphStatistics
)

logger = logging.getLogger("graph.service")

MAX_GRAPH_NODES = 250
MAX_GRAPH_EDGES = 600

class GraphService:
    """
    Application service managing database-backed blockchain graph operations,
    multi-hop BFS traversal, path discovery, and counterparty aggregation.
    """

    @staticmethod
    def validate_wallet_address(address: str) -> bool:
        if not address or not isinstance(address, str):
            return False
        return bool(re.match(r"^0x[a-fA-F0-9]{40}$", address.strip()))

    @classmethod
    def build_wallet_graph(
        cls,
        db: Session,
        wallet_address: str,
        max_hops: int = 3,
        direction: str = "both",
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None,
        start_timestamp: Optional[str] = None,
        end_timestamp: Optional[str] = None
    ) -> GraphResponse:
        """
        Builds a multi-hop directed transaction graph using BFS against stored PostgreSQL records.
        """
        if not cls.validate_wallet_address(wallet_address):
            raise ValueError("Invalid Ethereum wallet address format")

        if not (1 <= max_hops <= 5):
            raise ValueError("max_hops must be an integer between 1 and 5")

        clean_dir = (direction or "both").lower().strip()
        if clean_dir not in ("incoming", "outgoing", "both"):
            raise ValueError("direction must be 'incoming', 'outgoing', or 'both'")

        norm_root = wallet_address.strip().lower()
        visited_wallets: Set[str] = {norm_root}
        current_frontier: Set[str] = {norm_root}
        node_hops: Dict[str, int] = {norm_root: 0}

        collected_txs: List[Transaction] = []
        collected_tx_hashes: Set[str] = set()
        is_truncated = False
        warning = None

        labels_map = {}
        try:
            for lbl in db.query(AddressLabel).all():
                if hasattr(lbl, "address") and lbl.address:
                    labels_map[lbl.address.lower()] = lbl
        except Exception:
            labels_map = {}

        # Multi-hop BFS traversal against PostgreSQL
        for hop in range(1, max_hops + 1):
            if not current_frontier:
                break

            # Build query for the current frontier (case-insensitive)
            frontier_list = [a.lower() for a in current_frontier]
            conditions = []
            if clean_dir in ("outgoing", "both"):
                conditions.append(func.lower(Transaction.from_address).in_(frontier_list))
            if clean_dir in ("incoming", "both"):
                conditions.append(func.lower(Transaction.to_address).in_(frontier_list))

            if not conditions:
                break

            query = db.query(Transaction).filter(or_(*conditions))

            # Apply transaction filters
            if min_value is not None:
                query = query.filter(Transaction.value_eth >= min_value)
            if max_value is not None:
                query = query.filter(Transaction.value_eth <= max_value)
            if from_block is not None:
                query = query.filter(Transaction.block_number >= from_block)
            if to_block is not None:
                query = query.filter(Transaction.block_number <= to_block)
            if start_timestamp is not None:
                query = query.filter(Transaction.block_timestamp >= start_timestamp)
            if end_timestamp is not None:
                query = query.filter(Transaction.block_timestamp <= end_timestamp)

            hop_txs = query.order_by(desc(Transaction.block_number)).limit(MAX_GRAPH_EDGES).all()

            next_frontier: Set[str] = set()
            for tx in hop_txs:
                tx_h = getattr(tx, "tx_hash", None) or getattr(tx, "transaction_hash", "")
                if tx_h in collected_tx_hashes:
                    continue
                collected_tx_hashes.add(tx_h)
                collected_txs.append(tx)

                u = (tx.from_address or "").lower()
                v = (tx.to_address or "").lower()

                # Identify next-hop counterparties
                if clean_dir in ("outgoing", "both") and u in current_frontier and v and v not in visited_wallets:
                    visited_wallets.add(v)
                    node_hops[v] = hop
                    next_frontier.add(v)

                if clean_dir in ("incoming", "both") and v in current_frontier and u and u not in visited_wallets:
                    visited_wallets.add(u)
                    node_hops[u] = hop
                    next_frontier.add(u)

                # Check display limits
                if len(visited_wallets) >= MAX_GRAPH_NODES or len(collected_txs) >= MAX_GRAPH_EDGES:
                    is_truncated = True
                    warning = "Graph truncated because the result exceeds the configured display limit."
                    break

            if is_truncated:
                break

            current_frontier = next_frontier

        # Construct NetworkX graph using GraphBuilder
        builder = GraphBuilder()
        builder.populate_from_transactions(
            transactions=collected_txs,
            labels_map=labels_map,
            root_wallet=norm_root,
            node_hops=node_hops
        )

        # Ensure root node exists even if 0 transactions were found
        if not builder.get_graph().has_node(norm_root):
            builder.get_graph().add_node(
                norm_root,
                id=norm_root,
                address=norm_root,
                blockchain="Ethereum",
                label="suspect",
                entity_type="UNKNOWN",
                transaction_count=0,
                incoming_count=0,
                outgoing_count=0,
                total_incoming_value=0.0,
                total_outgoing_value=0.0,
                hops_from_root=0,
                is_root=True
            )

        return builder.to_graph_response(
            root_wallet=norm_root,
            max_hops=max_hops,
            direction=clean_dir,
            is_truncated=is_truncated,
            warning=warning
        )

    @classmethod
    def get_wallet_paths(
        cls,
        db: Session,
        wallet_address: str,
        max_hops: int = 3,
        direction: str = "both",
        min_value: Optional[float] = None
    ) -> PathDiscoveryResponse:
        """
        Discovers money-flow paths bounded by max_hops from or to the given wallet address.
        """
        if not cls.validate_wallet_address(wallet_address):
            raise ValueError("Invalid Ethereum wallet address format")

        if not (1 <= max_hops <= 5):
            raise ValueError("max_hops must be an integer between 1 and 5")

        graph_resp = cls.build_wallet_graph(
            db=db,
            wallet_address=wallet_address,
            max_hops=max_hops,
            direction=direction,
            min_value=min_value
        )

        # Build NetworkX representation for path analysis
        builder = GraphBuilder()
        builder.populate_from_transactions(
            transactions=graph_resp.edges,
            root_wallet=wallet_address,
            node_hops={n.address: n.hops_from_root for n in graph_resp.nodes}
        )

        analyzer = PathAnalyzer(builder.get_graph())
        paths = analyzer.discover_money_flow_paths(
            root_wallet=wallet_address,
            max_hops=max_hops,
            direction=direction,
            min_value=min_value
        )

        return PathDiscoveryResponse(
            root_wallet=wallet_address.lower().strip(),
            max_hops=max_hops,
            direction=direction,
            paths=paths,
            total_paths=len(paths)
        )

    @classmethod
    def get_wallet_counterparties(
        cls,
        db: Session,
        wallet_address: str
    ) -> CounterpartiesResponse:
        """
        Aggregates direct incoming senders and outgoing recipients for a wallet based on stored transactions.
        """
        if not cls.validate_wallet_address(wallet_address):
            raise ValueError("Invalid Ethereum wallet address format")

        norm_addr = wallet_address.strip().lower()

        # Outgoing transactions: from_address == norm_addr
        out_txs = db.query(Transaction).filter(
            func.lower(Transaction.from_address) == norm_addr
        ).all()

        # Incoming transactions: to_address == norm_addr
        in_txs = db.query(Transaction).filter(
            func.lower(Transaction.to_address) == norm_addr
        ).all()

        # Aggregate outgoing counterparties
        out_map: Dict[str, Dict[str, Any]] = {}
        for tx in out_txs:
            recipient = (tx.to_address or "").lower()
            if not recipient or recipient == norm_addr:
                continue
            if recipient not in out_map:
                out_map[recipient] = {"count": 0, "total_value": 0.0, "latest_block": None}
            out_map[recipient]["count"] += 1
            out_map[recipient]["total_value"] += float(tx.value_eth or 0.0)
            if tx.block_number:
                prev_blk = out_map[recipient]["latest_block"]
                out_map[recipient]["latest_block"] = max(prev_blk or 0, tx.block_number)

        # Aggregate incoming counterparties
        in_map: Dict[str, Dict[str, Any]] = {}
        for tx in in_txs:
            sender = (tx.from_address or "").lower()
            if not sender or sender == norm_addr:
                continue
            if sender not in in_map:
                in_map[sender] = {"count": 0, "total_value": 0.0, "latest_block": None}
            in_map[sender]["count"] += 1
            in_map[sender]["total_value"] += float(tx.value_eth or 0.0)
            if tx.block_number:
                prev_blk = in_map[sender]["latest_block"]
                in_map[sender]["latest_block"] = max(prev_blk or 0, tx.block_number)

        out_list = [
            CounterpartyDetail(
                address=addr,
                transaction_count=data["count"],
                total_value_eth=round(data["total_value"], 6),
                latest_block=data["latest_block"]
            )
            for addr, data in sorted(out_map.items(), key=lambda x: x[1]["total_value"], reverse=True)
        ]

        in_list = [
            CounterpartyDetail(
                address=addr,
                transaction_count=data["count"],
                total_value_eth=round(data["total_value"], 6),
                latest_block=data["latest_block"]
            )
            for addr, data in sorted(in_map.items(), key=lambda x: x[1]["total_value"], reverse=True)
        ]

        total_unique = len(set(out_map.keys()) | set(in_map.keys()))

        return CounterpartiesResponse(
            wallet=norm_addr,
            incoming=in_list,
            outgoing=out_list,
            total_unique_counterparties=total_unique
        )

    @classmethod
    def get_case_graph(
        cls,
        db: Session,
        case_id: str,
        max_hops: int = 3,
        direction: str = "both",
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None
    ) -> GraphResponse:
        """
        Validates case, retrieves suspect wallet, and constructs multi-hop transaction graph.
        """
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise ValueError(f"Case with ID '{case_id}' not found")
        if not case.suspect_wallet:
            raise ValueError(f"Case '{case_id}' does not have an associated suspect wallet")

        return cls.build_wallet_graph(
            db=db,
            wallet_address=case.suspect_wallet,
            max_hops=max_hops,
            direction=direction,
            min_value=min_value,
            max_value=max_value,
            from_block=from_block,
            to_block=to_block
        )
