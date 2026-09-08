import logging
import networkx as nx
from typing import List, Dict, Any, Optional, Set
from app.database.models import Transaction, AddressLabel, EntityType
from app.graph.graph_models import GraphNode, GraphEdge, GraphStatistics, GraphResponse

logger = logging.getLogger("graph.builder")

class GraphBuilder:
    """
    Constructs and analyzes directed NetworkX multigraphs from stored blockchain transactions.
    Wallets = Nodes, Transactions = Directed Edges (from_address -> to_address).
    """

    def __init__(self):
        self.g = nx.MultiDiGraph()
        self.node_hops: Dict[str, int] = {}
        self.root_wallet: Optional[str] = None

    def add_transaction(
        self,
        tx: Any,
        labels_map: Optional[Dict[str, AddressLabel]] = None,
        target_wallet: Optional[str] = None
    ):
        """
        Adds a transaction as a directed edge and updates endpoint wallet nodes.
        Supports both Phase 1 and Phase 3 Transaction models.
        """
        raw_u = getattr(tx, "from_address", None)
        raw_v = getattr(tx, "to_address", None)
        if not raw_u or not raw_v:
            return

        u = str(raw_u).strip().lower()
        v = str(raw_v).strip().lower()

        # Extract transaction identifiers and values
        tx_hash = (
            getattr(tx, "tx_hash", None)
            or getattr(tx, "transaction_hash", None)
            or f"0x{abs(hash((u, v, getattr(tx, 'block_number', 0))))}"
        )
        if hasattr(tx_hash, "hex"):
            tx_hash = tx_hash.hex()
        tx_hash = str(tx_hash).strip()
        if not tx_hash.startswith("0x"):
            tx_hash = "0x" + tx_hash

        val_eth = getattr(tx, "value_eth", None)
        if val_eth is None:
            val_eth = getattr(tx, "amount_native", 0.0) or 0.0
        try:
            val_eth = float(val_eth)
        except Exception:
            val_eth = 0.0

        val_wei = getattr(tx, "value_wei", None)
        if not val_wei:
            val_wei = str(int(val_eth * 1e18))

        block_num = getattr(tx, "block_number", None)
        block_ts = getattr(tx, "block_timestamp", None) or getattr(tx, "timestamp", None)
        block_ts_str = block_ts.isoformat() if hasattr(block_ts, "isoformat") else (str(block_ts) if block_ts else None)
        status = getattr(tx, "receipt_status", None) or getattr(tx, "status", "SUCCESS")
        tx_type = getattr(tx, "transaction_type", "native_transfer")

        # Initialize Node U (sender) if missing
        if not self.g.has_node(u):
            lbl_u = labels_map.get(u) if labels_map else None
            etype_u = lbl_u.entity_type.value if lbl_u and hasattr(lbl_u.entity_type, "value") else (str(lbl_u.entity_type) if lbl_u else "UNKNOWN")
            ename_u = lbl_u.entity_name if lbl_u else None
            conf_u = lbl_u.confidence.value if lbl_u and hasattr(lbl_u.confidence, "value") else (str(lbl_u.confidence) if lbl_u else None)
            self.g.add_node(
                u,
                id=u,
                address=u,
                blockchain="Ethereum",
                label=ename_u or "wallet",
                entity_type=etype_u,
                entity_name=ename_u,
                label_confidence=conf_u,
                transaction_count=0,
                incoming_count=0,
                outgoing_count=0,
                total_incoming_value=0.0,
                total_outgoing_value=0.0,
                hops_from_root=self.node_hops.get(u, 999),
                is_root=(u == self.root_wallet)
            )

        # Initialize Node V (recipient) if missing
        if not self.g.has_node(v):
            lbl_v = labels_map.get(v) if labels_map else None
            etype_v = lbl_v.entity_type.value if lbl_v and hasattr(lbl_v.entity_type, "value") else (str(lbl_v.entity_type) if lbl_v else "UNKNOWN")
            ename_v = lbl_v.entity_name if lbl_v else None
            conf_v = lbl_v.confidence.value if lbl_v and hasattr(lbl_v.confidence, "value") else (str(lbl_v.confidence) if lbl_v else None)
            self.g.add_node(
                v,
                id=v,
                address=v,
                blockchain="Ethereum",
                label=ename_v or "wallet",
                entity_type=etype_v,
                entity_name=ename_v,
                label_confidence=conf_v,
                transaction_count=0,
                incoming_count=0,
                outgoing_count=0,
                total_incoming_value=0.0,
                total_outgoing_value=0.0,
                hops_from_root=self.node_hops.get(v, 999),
                is_root=(v == self.root_wallet)
            )

        # Avoid duplicate edge insertion for the same transaction hash
        edge_key = f"{tx_hash}_{u}_{v}"
        if not self.g.has_edge(u, v, key=edge_key):
            # Update sender node counters
            self.g.nodes[u]["outgoing_count"] += 1
            self.g.nodes[u]["transaction_count"] += 1
            self.g.nodes[u]["total_outgoing_value"] = round(
                self.g.nodes[u]["total_outgoing_value"] + val_eth, 6
            )

            # Update recipient node counters
            self.g.nodes[v]["incoming_count"] += 1
            self.g.nodes[v]["transaction_count"] += 1
            self.g.nodes[v]["total_incoming_value"] = round(
                self.g.nodes[v]["total_incoming_value"] + val_eth, 6
            )

            # Determine direction relative to target / root wallet
            direction = "outgoing"
            if target_wallet and v == target_wallet.lower():
                direction = "incoming"

            # Add directed edge: u (from) -> v (to)
            self.g.add_edge(
                u,
                v,
                key=edge_key,
                id=f"{u}->{v}:{tx_hash}",
                tx_hash=tx_hash,
                transaction_hash=tx_hash,  # Backward compatibility
                from_address=u,
                to_address=v,
                value_wei=str(val_wei),
                value_eth=val_eth,
                amount=val_eth,  # Backward compatibility
                amount_native=val_eth,  # Backward compatibility
                amount_usd=getattr(tx, "amount_usd_if_available", None),
                block_number=block_num,
                block_timestamp=block_ts_str,
                timestamp=block_ts_str,  # Backward compatibility
                status=status,
                receipt_status=status,
                transaction_type=tx_type,
                direction=direction,
                blockchain="Ethereum"
            )

    def populate_from_transactions(
        self,
        transactions: List[Any],
        labels_map: Optional[Dict[str, AddressLabel]] = None,
        root_wallet: Optional[str] = None,
        node_hops: Optional[Dict[str, int]] = None
    ):
        """Populates the graph from an iterable of transactions."""
        if root_wallet:
            self.root_wallet = root_wallet.strip().lower()
        if node_hops:
            self.node_hops = {k.lower(): v for k, v in node_hops.items()}

        for tx in transactions:
            self.add_transaction(tx, labels_map=labels_map, target_wallet=self.root_wallet)

    def get_graph(self) -> nx.MultiDiGraph:
        """Returns the underlying NetworkX MultiDiGraph instance."""
        return self.g

    def compute_statistics(self, root_wallet: str) -> GraphStatistics:
        """Computes descriptive graph statistics without risk scoring."""
        norm_root = root_wallet.strip().lower()
        unique_nodes = set(self.g.nodes())
        counterparties = unique_nodes - {norm_root}

        incoming_conns = 0
        outgoing_conns = 0
        total_in_val = 0.0
        total_out_val = 0.0
        max_hop = 0

        # Compute direct root wallet interactions
        if self.g.has_node(norm_root):
            incoming_conns = len(list(self.g.predecessors(norm_root)))
            outgoing_conns = len(list(self.g.successors(norm_root)))
            total_in_val = self.g.nodes[norm_root].get("total_incoming_value", 0.0)
            total_out_val = self.g.nodes[norm_root].get("total_outgoing_value", 0.0)

        for n, data in self.g.nodes(data=True):
            h = data.get("hops_from_root", 0)
            if h != 999 and h > max_hop:
                max_hop = h

        return GraphStatistics(
            connected_wallets_count=len(counterparties),
            incoming_connections_count=incoming_conns,
            outgoing_connections_count=outgoing_conns,
            transaction_count=self.g.number_of_edges(),
            total_incoming_value_eth=round(total_in_val, 6),
            total_outgoing_value_eth=round(total_out_val, 6),
            max_hop_reached=max_hop,
            unique_counterparties=len(counterparties)
        )

    def to_graph_response(
        self,
        root_wallet: str,
        max_hops: int = 3,
        direction: str = "both",
        is_truncated: bool = False,
        warning: Optional[str] = None
    ) -> GraphResponse:
        """Serializes the graph into a structured GraphResponse."""
        norm_root = root_wallet.strip().lower()

        # Build GraphNode list
        nodes_list = []
        for node_id, data in self.g.nodes(data=True):
            is_root = (node_id == norm_root)
            label = "suspect" if is_root else data.get("label", "wallet")
            if label not in ("suspect", "wallet", "unknown"):
                # Clean label: keep descriptive or fallback to wallet
                label = "wallet"

            nodes_list.append(
                GraphNode(
                    id=node_id,
                    address=node_id,
                    blockchain=data.get("blockchain", "Ethereum"),
                    label=label,
                    entity_type=data.get("entity_type", "UNKNOWN"),
                    entity_name=data.get("entity_name"),
                    label_confidence=data.get("label_confidence"),
                    transaction_count=data.get("transaction_count", 0),
                    incoming_count=data.get("incoming_count", 0),
                    outgoing_count=data.get("outgoing_count", 0),
                    total_incoming_value=round(data.get("total_incoming_value", 0.0), 6),
                    total_outgoing_value=round(data.get("total_outgoing_value", 0.0), 6),
                    hops_from_root=self.node_hops.get(node_id, data.get("hops_from_root", 0)),
                    is_root=is_root
                )
            )

        # Build GraphEdge list
        edges_list = []
        for u, v, key, data in self.g.edges(keys=True, data=True):
            edges_list.append(
                GraphEdge(
                    id=data.get("id", f"{u}->{v}:{data.get('tx_hash', key)}"),
                    tx_hash=data.get("tx_hash", key),
                    from_address=u,
                    to_address=v,
                    value_wei=str(data.get("value_wei", "0")),
                    value_eth=float(data.get("value_eth", 0.0)),
                    block_number=data.get("block_number"),
                    block_timestamp=data.get("block_timestamp"),
                    direction=data.get("direction", "outgoing"),
                    transaction_type=data.get("transaction_type", "native_transfer")
                )
            )

        stats = self.compute_statistics(root_wallet=norm_root)

        return GraphResponse(
            root_wallet=norm_root,
            blockchain="Ethereum",
            chain_id=11155111,
            max_hops=max_hops,
            direction=direction,
            nodes=nodes_list,
            edges=edges_list,
            statistics=stats,
            is_truncated=is_truncated,
            warning=warning
        )
