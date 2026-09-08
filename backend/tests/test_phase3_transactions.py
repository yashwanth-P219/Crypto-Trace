import pytest
import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.database.database import get_db, SessionLocal
from app.database.models import Transaction, Case, CaseTransaction, Wallet
from app.blockchain.transaction_parser import TransactionNormalizer, NormalizedTransaction
from app.services.transaction_service import TransactionService

client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. Transaction Model & Uniqueness
def test_transaction_model_and_uniqueness(db_session: Session):
    unique_hash = f"0xtest_{datetime.datetime.utcnow().timestamp()}"
    tx1 = Transaction(
        tx_hash=unique_hash,
        blockchain="Ethereum",
        chain_id=11155111,
        block_number=123456,
        from_address="0x1111111111111111111111111111111111111111",
        to_address="0x2222222222222222222222222222222222222222",
        value_wei="1000000000000000000",
        value_eth=1.0,
        receipt_status="SUCCESS",
        transaction_type="native_transfer"
    )
    db_session.add(tx1)
    db_session.commit()
    assert tx1.id is not None
    assert tx1.transaction_hash == unique_hash
    assert tx1.amount_native == 1.0

    # Test uniqueness constraint
    tx2 = Transaction(
        tx_hash=unique_hash,
        blockchain="Ethereum",
        chain_id=11155111,
        from_address="0x3333333333333333333333333333333333333333",
        to_address="0x4444444444444444444444444444444444444444",
        value_wei="500000000000000000",
        value_eth=0.5
    )
    db_session.add(tx2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

# 2. Transaction Normalization & Classification
def test_transaction_normalization_native_and_direction():
    raw_data = {
        "hash": "0xABCDEF1234567890",
        "from": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
        "to": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "value": "2000000000000000000",
        "gas": "21000",
        "gasPrice": "20000000000",
        "blockNumber": "11000000",
        "timeStamp": "1700000000",
        "input": "0x",
        "isError": "0"
    }
    # Outgoing test from sender
    norm_outgoing = TransactionNormalizer.from_explorer_dict(
        raw_data, chain_id=11155111, target_wallet="0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
    )
    assert norm_outgoing.direction == "outgoing"
    assert norm_outgoing.value_eth == 2.0
    assert norm_outgoing.transaction_type == "native_transfer"
    assert norm_outgoing.receipt_status == "SUCCESS"

    # Incoming test from receiver
    norm_incoming = TransactionNormalizer.from_explorer_dict(
        raw_data, chain_id=11155111, target_wallet="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    )
    assert norm_incoming.direction == "incoming"

    # Contract interaction test
    raw_data_contract = dict(raw_data, input="0xa9059cbb000000000000000000000000")
    norm_contract = TransactionNormalizer.from_explorer_dict(raw_data_contract)
    assert norm_contract.transaction_type == "contract_interaction"

# 3. Address Validation API
def test_api_wallet_validate():
    resp_valid = client.get("/wallets/0xd8da6bf26964af9d7eed9e03e53415d37aa96045/validate")
    assert resp_valid.status_code == 200
    assert resp_valid.json()["is_valid"] is True

    resp_invalid = client.get("/wallets/0xBadAddress123/validate")
    assert resp_invalid.status_code == 200
    assert resp_invalid.json()["is_valid"] is False

# 4. Pagination & Filtering
def test_wallet_transactions_pagination(db_session: Session):
    addr = "0x9999999999999999999999999999999999999999"
    # Seed 5 transactions for this address
    for i in range(5):
        t = Transaction(
            tx_hash=f"0xpage_test_{i}_{datetime.datetime.utcnow().timestamp()}",
            blockchain="Ethereum",
            chain_id=11155111,
            block_number=1000 + i,
            from_address=addr if i % 2 == 0 else "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            to_address="0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" if i % 2 == 0 else addr,
            value_wei="1000000000000000000",
            value_eth=1.0,
            receipt_status="SUCCESS"
        )
        db_session.add(t)
    db_session.commit()

    # Request page 1 with page_size=2
    resp = client.get(f"/wallets/{addr}/transactions?page=1&page_size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= 5
    assert len(data["transactions"]) == 2

    # Request with incoming direction filter
    resp_in = client.get(f"/wallets/{addr}/transactions?direction=incoming")
    assert resp_in.status_code == 200
    for tx in resp_in.json()["transactions"]:
        assert tx["direction"] == "incoming"

# 5. Synchronization & Duplicate Prevention
def test_wallet_transaction_sync_mocked(db_session: Session):
    addr = "0x8888888888888888888888888888888888888888"
    mock_txs = [
        {
            "hash": f"0xmock_sync_1_{datetime.datetime.utcnow().timestamp()}",
            "from": addr,
            "to": "0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
            "value": "1500000000000000000",
            "gas": "21000",
            "gasPrice": "3000000000",
            "blockNumber": "11500001",
            "timeStamp": "1710000000",
            "isError": "0"
        }
    ]
    with patch("app.blockchain.history_provider.SepoliaHistoryProvider.get_transactions_for_address", return_value=mock_txs):
        # First sync: 1 inserted
        resp1 = client.post(f"/wallets/{addr}/transactions/sync")
        assert resp1.status_code == 200
        res1 = resp1.json()
        assert res1["fetched"] == 1
        assert res1["inserted"] == 1
        assert res1["duplicates"] == 0

        # Second sync: duplicate detected, 0 inserted, 1 duplicate
        resp2 = client.post(f"/wallets/{addr}/transactions/sync")
        assert resp2.status_code == 200
        res2 = resp2.json()
        assert res2["inserted"] == 0
        assert res2["duplicates"] == 1

# 6. Database-First Caching & Detail API
def test_transaction_detail_caching(db_session: Session):
    test_hash = f"0xcache_test_{datetime.datetime.utcnow().timestamp()}"
    tx = Transaction(
        tx_hash=test_hash,
        blockchain="Ethereum",
        chain_id=11155111,
        from_address="0x1111111111111111111111111111111111111111",
        to_address="0x2222222222222222222222222222222222222222",
        value_wei="3000000000000000000",
        value_eth=3.0,
        receipt_status="SUCCESS"
    )
    db_session.add(tx)
    db_session.commit()

    # Query endpoint: should return from DB cache
    resp = client.get(f"/transactions/{test_hash}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tx_hash"] == test_hash
    assert data["source"] == "database_cache"

# 7. Error Handling & Non-Existent Tx
def test_transaction_not_found():
    non_existent = "0x999999999999999999999999999999999999999999999999999999999999dead"
    with patch("app.blockchain.history_provider.SepoliaHistoryProvider.get_transaction", return_value=None):
        resp = client.get(f"/transactions/{non_existent}")
        assert resp.status_code == 404

def test_invalid_wallet_error_handling():
    resp = client.get("/wallets/0xNotAValidHex/transactions")
    assert resp.status_code == 400
    assert "Invalid Ethereum wallet address" in resp.json()["error"]

# 8. Database Status Endpoint
def test_database_status_endpoint():
    resp = client.get("/database/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "connected"
    assert "tables" in data
    assert "transactions" in data["tables"]

# 9. Case Transaction Association
def test_case_transaction_sync(db_session: Session):
    case_id = f"CASE-{datetime.datetime.utcnow().timestamp()}"
    suspect_addr = "0x7777777777777777777777777777777777777777"
    case = Case(
        case_id=case_id,
        victim_name="Test Victim",
        complaint_reference=f"REF-{case_id}",
        amount_lost=1.0,
        incident_date=datetime.datetime.utcnow(),
        suspect_wallet=suspect_addr,
        status="NEW"
    )
    db_session.add(case)
    db_session.commit()

    mock_txs = [
        {
            "hash": f"0xcase_tx_{datetime.datetime.utcnow().timestamp()}",
            "from": suspect_addr,
            "to": "0x1111111111111111111111111111111111111111",
            "value": "1000000000000000000",
            "gas": "21000",
            "blockNumber": "11500000",
            "isError": "0"
        }
    ]
    with patch("app.blockchain.history_provider.SepoliaHistoryProvider.get_transactions_for_address", return_value=mock_txs):
        resp = client.post(f"/cases/{case_id}/transactions/sync")
        assert resp.status_code == 200
        assert resp.json()["inserted"] == 1

        # Verify association in CaseTransaction
        assoc = db_session.query(CaseTransaction).filter(CaseTransaction.case_id == case_id).first()
        assert assoc is not None
