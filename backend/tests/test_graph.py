import datetime
import pytest
from app.database.models import Transaction, AddressLabel, EntityType, ConfidenceLevel
from app.graph.graph_builder import GraphBuilder
from app.graph.path_analysis import PathAnalyzer

def create_sample_chain():
    now = datetime.datetime.utcnow()
    # A -> B -> F -> VASP
    tx1 = Transaction(
        transaction_hash="0x01",
        blockchain="Ethereum",
        block_number=100,
        timestamp=now,
        from_address="0xAAAA",
        to_address="0xBBBB",
        amount_native=2.5,
        status="SUCCESS"
    )
    tx2 = Transaction(
        transaction_hash="0x02",
        blockchain="Ethereum",
        block_number=101,
        timestamp=now + datetime.timedelta(minutes=5),
        from_address="0xBBBB",
        to_address="0xFFFF",
        amount_native=1.5,
        status="SUCCESS"
    )
    tx3 = Transaction(
        transaction_hash="0x03",
        blockchain="Ethereum",
        block_number=102,
        timestamp=now + datetime.timedelta(minutes=10),
        from_address="0xFFFF",
        to_address="0xVASP",
        amount_native=1.4,
        status="SUCCESS"
    )

    labels = {
        "0xvasp": AddressLabel(
            address="0xVASP",
            blockchain="Ethereum",
            entity_name="Test Exchange VASP",
            entity_type=EntityType.VASP,
            source="Intel",
            confidence=ConfidenceLevel.HIGH
        )
    }
    return [tx1, tx2, tx3], labels

def test_graph_builder_and_k_hop():
    txs, labels = create_sample_chain()
    gb = GraphBuilder()
    gb.populate_from_transactions(txs, labels)
    g = gb.get_graph()

    assert g.number_of_nodes() == 4
    assert g.number_of_edges() == 3

    pa = PathAnalyzer(g)
    subgraph_1hop = pa.get_k_hop_subgraph("0xAAAA", max_hops=1)
    assert subgraph_1hop["node_count"] == 2 # 0xAAAA and 0xBBBB
    assert subgraph_1hop["edge_count"] == 1

    subgraph_3hop = pa.get_k_hop_subgraph("0xAAAA", max_hops=3)
    assert subgraph_3hop["node_count"] == 4
    assert subgraph_3hop["edge_count"] == 3

def test_path_tracing_to_vasp():
    txs, labels = create_sample_chain()
    gb = GraphBuilder()
    gb.populate_from_transactions(txs, labels)
    g = gb.get_graph()

    pa = PathAnalyzer(g)
    vasp_paths = pa.trace_paths_to_vasp("0xAAAA", max_hops=5)

    assert len(vasp_paths) == 1
    p = vasp_paths[0]
    assert p["hops"] == 3
    assert p["destination_vasp"] == "Test Exchange VASP"
    assert len(p["steps"]) == 3
