import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class GraphNode(BaseModel):
    id: str
    address: str
    blockchain: str = "Ethereum"
    label: str = "unknown"  # "suspect" | "wallet" | "unknown"
    entity_type: str = "UNKNOWN"
    entity_name: Optional[str] = None
    label_confidence: Optional[str] = None
    transaction_count: int = 0
    incoming_count: int = 0
    outgoing_count: int = 0
    total_incoming_value: float = 0.0
    total_outgoing_value: float = 0.0
    hops_from_root: int = 0
    is_root: bool = False

class GraphEdge(BaseModel):
    id: str
    tx_hash: str
    from_address: str
    to_address: str
    value_wei: str = "0"
    value_eth: float = 0.0
    block_number: Optional[int] = None
    block_timestamp: Optional[str] = None
    direction: str = "outgoing"  # "outgoing" | "incoming"
    transaction_type: str = "native_transfer"  # "native_transfer" | "contract_interaction"

class GraphStatistics(BaseModel):
    connected_wallets_count: int = 0
    incoming_connections_count: int = 0
    outgoing_connections_count: int = 0
    transaction_count: int = 0
    total_incoming_value_eth: float = 0.0
    total_outgoing_value_eth: float = 0.0
    max_hop_reached: int = 0
    unique_counterparties: int = 0

class GraphResponse(BaseModel):
    root_wallet: str
    blockchain: str = "Ethereum"
    chain_id: int = 11155111
    max_hops: int = 3
    direction: str = "both"
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    statistics: GraphStatistics
    is_truncated: bool = False
    warning: Optional[str] = None

class PathDiscoveryResponse(BaseModel):
    root_wallet: str
    max_hops: int
    direction: str
    paths: List[List[str]]
    total_paths: int

class CounterpartyDetail(BaseModel):
    address: str
    transaction_count: int
    total_value_eth: float
    latest_block: Optional[int] = None

class CounterpartiesResponse(BaseModel):
    wallet: str
    incoming: List[CounterpartyDetail]
    outgoing: List[CounterpartyDetail]
    total_unique_counterparties: int
