import pytest
import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import networkx as nx

from app.main import app
from app.database.database import SessionLocal
from app.database.models import Transaction, Case, AddressLabel, EntityType
from app.analysis.pattern_rules import PatternRules
from app.analysis.pattern_detector import PatternDetector
from app.analysis.pattern_service import PatternService

client = TestClient(app)

class MockTx:
    def __init__(self, tx_hash, from_addr, to_addr, val_eth, ts):
        self.tx_hash = tx_hash
        self.transaction_hash = tx_hash
        self.from_address = from_addr
        self.to_address = to_addr
        self.value_eth = val_eth
        self.amount_native = val_eth
        self.block_timestamp = ts
        self.timestamp = ts

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_rapid_transfer_detection():
    now = datetime.datetime.utcnow()
    wallet = "0x1111111111111111111111111111111111111111"
    txs = [
        MockTx("0xin1", "0xvictim", wallet, 5.0, now),
        MockTx("0xout1", wallet, "0xmule1", 4.9, now + datetime.timedelta(seconds=120))  # 2 mins later
    ]
    findings = PatternRules.detect_rapid_transfers(wallet, txs)
    assert len(findings) >= 1
    assert findings[0].pattern_id == "PAT-RAPID-TRANSFER"
    assert "0xin1" in findings[0].related_transaction_hashes
    assert "0xout1" in findings[0].related_transaction_hashes
    assert findings[0].evidence["time_difference_seconds"] == 120

def test_rapid_transfer_negative_beyond_window():
    now = datetime.datetime.utcnow()
    wallet = "0x1111111111111111111111111111111111111111"
    txs = [
        MockTx("0xin1", "0xvictim", wallet, 5.0, now),
        # 2 hours later - beyond 15 minute window
        MockTx("0xout1", wallet, "0xmule1", 4.9, now + datetime.timedelta(hours=2))
    ]
    findings = PatternRules.detect_rapid_transfers(wallet, txs)
    assert len(findings) == 0

def test_fund_splitting_detection():
    now = datetime.datetime.utcnow()
    wallet = "0x2222222222222222222222222222222222222222"
    txs = [
        MockTx("0xin1", "0xsource", wallet, 10.0, now),
        MockTx("0xout1", wallet, "0xdest1", 3.0, now + datetime.timedelta(minutes=5)),
        MockTx("0xout2", wallet, "0xdest2", 3.0, now + datetime.timedelta(minutes=6)),
        MockTx("0xout3", wallet, "0xdest3", 3.5, now + datetime.timedelta(minutes=7))
    ]
    findings = PatternRules.detect_fund_splitting(wallet, txs)
    assert len(findings) >= 1
    assert findings[0].pattern_id == "PAT-FUND-SPLITTING"
    assert findings[0].evidence["unique_destinations"] == 3
    assert len(findings[0].related_wallets) >= 3

def test_fund_consolidation_detection():
    now = datetime.datetime.utcnow()
    wallet = "0x3333333333333333333333333333333333333333"
    txs = [
        MockTx("0xin1", "0xsrc1", wallet, 2.0, now),
        MockTx("0xin2", "0xsrc2", wallet, 3.0, now + datetime.timedelta(minutes=1)),
        MockTx("0xin3", "0xsrc3", wallet, 4.0, now + datetime.timedelta(minutes=2)),
        MockTx("0xout1", wallet, "0xliquidation", 8.9, now + datetime.timedelta(minutes=10))
    ]
    findings = PatternRules.detect_fund_consolidation(wallet, txs)
    assert len(findings) >= 1
    assert findings[0].pattern_id == "PAT-FUND-CONSOLIDATION"
    assert findings[0].evidence["incoming_sources_count"] == 3

def test_multi_hop_movement_detection():
    wallet = "0x4444444444444444444444444444444444444444"
    paths = [
        [wallet, "0xhop1", "0xhop2", "0xdestination"]  # 3 hops
    ]
    findings = PatternRules.detect_multi_hop_movement(wallet, graph_paths=paths, max_hop_depth=3)
    assert len(findings) >= 1
    assert findings[0].pattern_id == "PAT-MULTI-HOP"
    assert findings[0].evidence["max_hop_depth"] == 3

def test_high_frequency_burst_detection():
    now = datetime.datetime.utcnow()
    wallet = "0x5555555555555555555555555555555555555555"
    # 12 transactions within 2 minutes = 6 tx/min (well above 0.5 tx/min threshold)
    txs = [
        MockTx(f"0xburst_{i}", wallet, f"0xdest_{i}", 0.1, now + datetime.timedelta(seconds=i*10))
        for i in range(12)
    ]
    findings = PatternRules.detect_high_frequency_burst(wallet, txs)
    assert len(findings) >= 1
    assert findings[0].pattern_id == "PAT-HIGH-FREQUENCY-BURST"
    assert findings[0].evidence["rate_per_minute"] > 1.0

def test_circular_movement_detection():
    wallet = "0x6666666666666666666666666666666666666666"
    g = nx.MultiDiGraph()
    g.add_edge(wallet, "0xnodeB", key="1")
    g.add_edge("0xnodeB", "0xnodeC", key="2")
    g.add_edge("0xnodeC", wallet, key="3")

    findings = PatternRules.detect_circular_movement(wallet, g)
    assert len(findings) >= 1
    assert findings[0].pattern_id == "PAT-CIRCULAR-FLOW"
    assert findings[0].evidence["cycle_length"] == 3

def test_sudden_large_transfer_detection():
    now = datetime.datetime.utcnow()
    wallet = "0x7777777777777777777777777777777777777777"
    txs = [
        MockTx("0xsmall1", wallet, "0xa", 0.05, now),
        MockTx("0xsmall2", wallet, "0xb", 0.05, now),
        MockTx("0xsmall3", wallet, "0xc", 0.05, now),
        MockTx("0xlarge", wallet, "0xd", 5.0, now)  # 100x median (0.05 ETH)
    ]
    findings = PatternRules.detect_sudden_large_transfer(wallet, txs)
    assert len(findings) >= 1
    assert findings[0].pattern_id == "PAT-SUDDEN-LARGE-TRANSFER"
    assert findings[0].evidence["outlier_amount_eth"] == 5.0

def test_unusual_counterparty_behavior_detection():
    now = datetime.datetime.utcnow()
    wallet = "0x8888888888888888888888888888888888888888"
    txs = [
        MockTx(f"0xcp_{i}", wallet, f"0xunique_dest_{i}", 0.1, now)
        for i in range(10)
    ]
    findings = PatternRules.detect_unusual_counterparty_behavior(wallet, txs)
    assert len(findings) >= 1
    assert findings[0].pattern_id == "PAT-UNUSUAL-COUNTERPARTY-SPREAD"
    assert findings[0].evidence["unique_counterparties_total"] >= 8

def test_empty_transaction_dataset():
    findings = PatternDetector.analyze_wallet("0xempty", [])
    assert findings == []

def test_pattern_api_endpoints():
    test_addr = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    res = client.get(f"/analysis/wallet/{test_addr}/patterns?max_hops=2")
    assert res.status_code == 200
    data = res.json()
    assert data["wallet_address"] == test_addr.lower()
    assert "patterns" in data
    assert "summary" in data

    # Invalid address
    res_bad = client.get("/analysis/wallet/invalid_address/patterns")
    assert res_bad.status_code == 400
