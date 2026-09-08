import datetime
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.database import Base, get_db, SessionLocal
from app.database.models import Transaction, Case, AddressLabel, EntityType
from app.graph.graph_builder import GraphBuilder
from app.graph.path_analysis import PathAnalyzer
from app.graph.graph_service import GraphService, MAX_GRAPH_NODES, MAX_GRAPH_EDGES
from app.graph.graph_models import GraphResponse, PathDiscoveryResponse, CounterpartiesResponse

client = TestClient(app)

# Deterministic test addresses
WALLET_A = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
WALLET_B = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
WALLET_C = "0xcccccccccccccccccccccccccccccccccccccccc"
WALLET_D = "0xdddddddddddddddddddddddddddddddddddddddd"
WALLET_E = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
WALLET_F = "0xffffffffffffffffffffffffffffffffffffffff"
WALLET_X = "0x1111111111111111111111111111111111111111"
WALLET_Y = "0x2222222222222222222222222222222222222222"

def create_deterministic_mock_txs():
    """
    Graph topology:
    Incoming: X -> Y -> A
    Outgoing: A -> B -> D -> F
              A -> C -> E
    """
    now = datetime.datetime.now(datetime.UTC)
    txs = [
        # Incoming to A
        Transaction(
            tx_hash="0xtx_xy",
            blockchain="Ethereum",
            chain_id=11155111,
            block_number=1000,
            from_address=WALLET_X,
            to_address=WALLET_Y,
            value_wei="1000000000000000000",
            value_eth=1.0,
            receipt_status="SUCCESS",
            block_timestamp=now
        ),
        Transaction(
            tx_hash="0xtx_ya",
            blockchain="Ethereum",
            chain_id=11155111,
            block_number=1001,
            from_address=WALLET_Y,
            to_address=WALLET_A,
            value_wei="1000000000000000000",
            value_eth=1.0,
            receipt_status="SUCCESS",
            block_timestamp=now
        ),
        # Outgoing from A
        Transaction(
            tx_hash="0xtx_ab",
            blockchain="Ethereum",
            chain_id=11155111,
            block_number=1002,
            from_address=WALLET_A,
            to_address=WALLET_B,
            value_wei="5000000000000000000",
            value_eth=5.0,
            receipt_status="SUCCESS",
            block_timestamp=now
        ),
        Transaction(
            tx_hash="0xtx_ac",
            blockchain="Ethereum",
            chain_id=11155111,
            block_number=1003,
            from_address=WALLET_A,
            to_address=WALLET_C,
            value_wei="2000000000000000000",
            value_eth=2.0,
            receipt_status="SUCCESS",
            block_timestamp=now
        ),
        Transaction(
            tx_hash="0xtx_bd",
            blockchain="Ethereum",
            chain_id=11155111,
            block_number=1004,
            from_address=WALLET_B,
            to_address=WALLET_D,
            value_wei="4000000000000000000",
            value_eth=4.0,
            receipt_status="SUCCESS",
            block_timestamp=now
        ),
        Transaction(
            tx_hash="0xtx_ce",
            blockchain="Ethereum",
            chain_id=11155111,
            block_number=1005,
            from_address=WALLET_C,
            to_address=WALLET_E,
            value_wei="1000000000000000000",
            value_eth=1.0,
            receipt_status="SUCCESS",
            block_timestamp=now
        ),
        Transaction(
            tx_hash="0xtx_df",
            blockchain="Ethereum",
            chain_id=11155111,
            block_number=1006,
            from_address=WALLET_D,
            to_address=WALLET_F,
            value_wei="3000000000000000000",
            value_eth=3.0,
            receipt_status="SUCCESS",
            block_timestamp=now
        )
    ]
    return txs

# 1. Graph Construction & Node/Edge Creation
def test_graph_builder_nodes_and_edges():
    txs = create_deterministic_mock_txs()
    builder = GraphBuilder()
    builder.populate_from_transactions(txs, root_wallet=WALLET_A)
    g = builder.get_graph()

    # Verify total unique nodes and edges
    assert g.number_of_nodes() == 8
    assert g.number_of_edges() == 7

    # Check root node
    assert g.nodes[WALLET_A]["is_root"] is True
    assert g.nodes[WALLET_A]["outgoing_count"] == 2
    assert g.nodes[WALLET_A]["incoming_count"] == 1
    assert g.nodes[WALLET_A]["total_outgoing_value"] == 7.0
    assert g.nodes[WALLET_A]["total_incoming_value"] == 1.0

    # Check edge attributes
    edge_data = list(g.get_edge_data(WALLET_A, WALLET_B).values())[0]
    assert edge_data["tx_hash"] == "0xtx_ab"
    assert edge_data["value_eth"] == 5.0
    assert edge_data["block_number"] == 1002
    assert edge_data["receipt_status"] == "SUCCESS"

# 2. Duplicate Node & Edge Handling
def test_duplicate_node_and_edge_deduplication():
    builder = GraphBuilder()
    tx1 = Transaction(
        tx_hash="0xdup1",
        from_address=WALLET_A,
        to_address=WALLET_B,
        value_eth=1.5,
        value_wei="1500000000000000000"
    )
    # Add same transaction twice
    builder.add_transaction(tx1)
    builder.add_transaction(tx1)
    g = builder.get_graph()

    assert g.number_of_nodes() == 2
    assert g.number_of_edges() == 1
    assert g.nodes[WALLET_A]["outgoing_count"] == 1

# 3. Path Analysis & Directional Tracing
def test_path_discovery_outgoing_incoming():
    txs = create_deterministic_mock_txs()
    builder = GraphBuilder()
    builder.populate_from_transactions(txs, root_wallet=WALLET_A)
    analyzer = PathAnalyzer(builder.get_graph())

    # Outgoing paths from A:
    # A -> B, A -> C, A -> B -> D, A -> C -> E, A -> B -> D -> F
    out_paths = analyzer.discover_money_flow_paths(root_wallet=WALLET_A, max_hops=3, direction="outgoing")
    assert len(out_paths) == 5
    assert [WALLET_A, WALLET_B] in out_paths
    assert [WALLET_A, WALLET_B, WALLET_D] in out_paths
    assert [WALLET_A, WALLET_B, WALLET_D, WALLET_F] in out_paths

    # Incoming paths to A:
    # Y -> A, X -> Y -> A
    in_paths = analyzer.discover_money_flow_paths(root_wallet=WALLET_A, max_hops=3, direction="incoming")
    assert len(in_paths) == 2
    assert [WALLET_Y, WALLET_A] in in_paths
    assert [WALLET_X, WALLET_Y, WALLET_A] in in_paths

    # Reachable wallets by hop
    hop_map = analyzer.get_reachable_wallets(root_wallet=WALLET_A, max_hops=3, direction="outgoing")
    assert hop_map[0] == [WALLET_A]
    assert set(hop_map[1]) == {WALLET_B, WALLET_C}
    assert set(hop_map[2]) == {WALLET_D, WALLET_E}
    assert set(hop_map[3]) == {WALLET_F}

# 4. Hop Depth Enforcement (1, 2, 3 hops)
def test_hop_depth_boundaries():
    txs = create_deterministic_mock_txs()
    builder = GraphBuilder()
    builder.populate_from_transactions(txs, root_wallet=WALLET_A)
    analyzer = PathAnalyzer(builder.get_graph())

    # 1 Hop: only immediate neighbors (B and C)
    paths_1hop = analyzer.discover_money_flow_paths(root_wallet=WALLET_A, max_hops=1, direction="outgoing")
    assert len(paths_1hop) == 2
    assert all(len(p) == 2 for p in paths_1hop)

    # 2 Hops: paths up to length 3 (A->B, A->C, A->B->D, A->C->E)
    paths_2hop = analyzer.discover_money_flow_paths(root_wallet=WALLET_A, max_hops=2, direction="outgoing")
    assert len(paths_2hop) == 4
    assert [WALLET_A, WALLET_B, WALLET_D, WALLET_F] not in paths_2hop

    # 3 Hops: includes F
    paths_3hop = analyzer.discover_money_flow_paths(root_wallet=WALLET_A, max_hops=3, direction="outgoing")
    assert [WALLET_A, WALLET_B, WALLET_D, WALLET_F] in paths_3hop

# 5. Descriptive Statistics Calculation
def test_graph_descriptive_statistics():
    txs = create_deterministic_mock_txs()
    builder = GraphBuilder()
    builder.populate_from_transactions(txs, root_wallet=WALLET_A)
    stats = builder.compute_statistics(root_wallet=WALLET_A)

    assert stats.connected_wallets_count == 7
    assert stats.incoming_connections_count == 1  # From Y
    assert stats.outgoing_connections_count == 2  # To B, C
    assert stats.transaction_count == 7
    assert stats.total_incoming_value_eth == 1.0
    assert stats.total_outgoing_value_eth == 7.0
    assert stats.unique_counterparties == 7

# 6. Database Service & Hop Traversal with In-Memory Session
def test_graph_service_build_wallet_graph():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)
    db = TestSession()

    try:
        txs = create_deterministic_mock_txs()
        db.add_all(txs)
        db.commit()

        # Test 1 Hop from WALLET_A
        resp_1hop = GraphService.build_wallet_graph(
            db=db,
            wallet_address=WALLET_A,
            max_hops=1,
            direction="both"
        )
        assert isinstance(resp_1hop, GraphResponse)
        assert resp_1hop.root_wallet == WALLET_A
        assert resp_1hop.max_hops == 1
        # Root A, plus immediate counterparties B, C, Y = 4 nodes
        assert len(resp_1hop.nodes) == 4
        # Edges: Y->A, A->B, A->C = 3 edges
        assert len(resp_1hop.edges) == 3

        # Test 3 Hops from WALLET_A
        resp_3hop = GraphService.build_wallet_graph(
            db=db,
            wallet_address=WALLET_A,
            max_hops=3,
            direction="both"
        )
        assert len(resp_3hop.nodes) == 8
        assert len(resp_3hop.edges) == 7
        assert resp_3hop.statistics.connected_wallets_count == 7
        assert resp_3hop.statistics.max_hop_reached == 3
    finally:
        db.close()

# 7. Counterparties Aggregation
def test_graph_service_counterparties():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)
    db = TestSession()

    try:
        txs = create_deterministic_mock_txs()
        db.add_all(txs)
        db.commit()

        counterparties = GraphService.get_wallet_counterparties(db=db, wallet_address=WALLET_A)
        assert isinstance(counterparties, CounterpartiesResponse)
        assert counterparties.wallet == WALLET_A
        assert counterparties.total_unique_counterparties == 3
        assert len(counterparties.outgoing) == 2
        assert len(counterparties.incoming) == 1
        assert counterparties.outgoing[0].address == WALLET_B
        assert counterparties.outgoing[0].total_value_eth == 5.0
        assert counterparties.incoming[0].address == WALLET_Y
        assert counterparties.incoming[0].total_value_eth == 1.0
    finally:
        db.close()

# 8. API Validation & Error Handling
def test_api_invalid_wallet_error():
    # Malformed wallet
    resp = client.get("/graph/wallet/0xInvalidHex")
    assert resp.status_code == 400
    assert "Invalid Ethereum wallet address" in resp.json()["error"]

    resp_paths = client.get("/graph/paths/0x123")
    assert resp_paths.status_code == 400

    resp_cp = client.get("/wallets/0x123/counterparties")
    assert resp_cp.status_code == 400

def test_api_max_hops_validation():
    # Hops > 5 rejected
    resp_over = client.get(f"/graph/wallet/{WALLET_A}?max_hops=6")
    assert resp_over.status_code == 422  # FastAPI query validation le=5

    # Hops < 1 rejected
    resp_under = client.get(f"/graph/wallet/{WALLET_A}?max_hops=0")
    assert resp_under.status_code == 422  # FastAPI query validation ge=1

def test_api_direction_validation():
    resp_bad_dir = client.get(f"/graph/wallet/{WALLET_A}?direction=diagonal")
    assert resp_bad_dir.status_code == 422  # Pattern validation

def test_api_case_graph_not_found():
    resp = client.get("/cases/CASE-NON-EXISTENT/graph")
    assert resp.status_code == 404
    assert "not found" in resp.json()["error"].lower()

# 9. Value and Block Filtering
def test_path_analyzer_min_value_filter():
    txs = create_deterministic_mock_txs()
    builder = GraphBuilder()
    builder.populate_from_transactions(txs, root_wallet=WALLET_A)
    analyzer = PathAnalyzer(builder.get_graph())

    # All outgoing paths from A: 5 paths
    all_paths = analyzer.discover_money_flow_paths(root_wallet=WALLET_A, max_hops=3, direction="outgoing")
    assert len(all_paths) == 5

    # Filter min_value = 3.5 ETH: only A -> B (5.0) -> D (4.0) should qualify
    filtered_paths = analyzer.discover_money_flow_paths(
        root_wallet=WALLET_A, max_hops=3, direction="outgoing", min_value=3.5
    )
    assert [WALLET_A, WALLET_B] in filtered_paths
    assert [WALLET_A, WALLET_B, WALLET_D] in filtered_paths
    assert [WALLET_A, WALLET_C] not in filtered_paths  # A->C is 2.0 ETH
    assert [WALLET_A, WALLET_B, WALLET_D, WALLET_F] not in filtered_paths  # D->F is 3.0 ETH

# 10. 5-Hop Tracing
def test_5_hop_traversal():
    WALLET_G = "0x7777777777777777777777777777777777777777"
    WALLET_H = "0x8888888888888888888888888888888888888888"
    now = datetime.datetime.now(datetime.UTC)
    txs = create_deterministic_mock_txs()
    # A -> B -> D -> F -> G -> H (5 hops)
    txs.append(Transaction(
        tx_hash="0xtx_fg",
        from_address=WALLET_F,
        to_address=WALLET_G,
        value_eth=2.0,
        receipt_status="SUCCESS",
        block_timestamp=now
    ))
    txs.append(Transaction(
        tx_hash="0xtx_gh",
        from_address=WALLET_G,
        to_address=WALLET_H,
        value_eth=1.5,
        receipt_status="SUCCESS",
        block_timestamp=now
    ))

    builder = GraphBuilder()
    builder.populate_from_transactions(txs, root_wallet=WALLET_A)
    analyzer = PathAnalyzer(builder.get_graph())

    paths_5hop = analyzer.discover_money_flow_paths(root_wallet=WALLET_A, max_hops=5, direction="outgoing")
    five_hop_path = [WALLET_A, WALLET_B, WALLET_D, WALLET_F, WALLET_G, WALLET_H]
    assert five_hop_path in paths_5hop

# 11. Empty Wallet Handling (0 Transactions)
def test_empty_wallet_handling():
    EMPTY_WALLET = f"0x{'9'*30}{int(datetime.datetime.now(datetime.UTC).timestamp())}"
    resp = client.get(f"/graph/wallet/{EMPTY_WALLET}?max_hops=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["root_wallet"] == EMPTY_WALLET.lower()
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["is_root"] is True
    assert len(data["edges"]) == 0
    assert data["statistics"]["transaction_count"] == 0

# 12. Case Graph API Integration
def test_case_graph_api_endpoint():
    # Demo case CASE-SIH2026-001 is seeded by conftest
    resp = client.get("/cases/CASE-SIH2026-001/graph?max_hops=3")
    assert resp.status_code == 200
    data = resp.json()
    assert "root_wallet" in data
    assert "nodes" in data
    assert "edges" in data
    assert "statistics" in data

# 13. Graph Truncation Safety Warning
def test_graph_truncation_warning():
    builder = GraphBuilder()
    resp = builder.to_graph_response(
        root_wallet=WALLET_A,
        max_hops=3,
        direction="both",
        is_truncated=True,
        warning="Graph truncated because the result exceeds the configured display limit."
    )
    assert resp.is_truncated is True
    assert "Graph truncated" in resp.warning
