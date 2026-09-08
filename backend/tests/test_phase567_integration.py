import pytest
import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database.database import SessionLocal
from app.database.models import Transaction, Case, AddressLabel, EntityType, ConfidenceLevel, AnalysisPattern, RiskAssessmentRecord
from app.entities.service import EntityService

client = TestClient(app)

def test_full_investigation_pipeline_e2e():
    """
    Integration test verifying the combined Phase 5 + Phase 6 + Phase 7 pipeline:
    A (Victim) -> B (Suspect Mule)
    B -> C (Intermediary 1)
    B -> D (Intermediary 2) [Splitting Pattern]
    C -> E (Known VASP / Exchange) [Multi-Hop to VASP Gateway]
    """
    db = SessionLocal()
    EntityService.seed_demo_intel(db)

    now = datetime.datetime.utcnow()

    # Define wallets
    wallet_a = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" # Victim
    wallet_b = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" # Suspect
    wallet_c = "0xcccccccccccccccccccccccccccccccccccccccc" # Intermediary 1
    wallet_d = "0xdddddddddddddddddddddddddddddddddddddddd" # Intermediary 2
    wallet_e = "0x28c6c06298d514db089934071355e5743bf21d60" # Binance Hot Wallet (Known VASP)

    # 1. Insert synthetic test case and transactions
    test_case_id = f"CASE-INTEG-{int(now.timestamp())}"
    test_case = Case(
        case_id=test_case_id,
        victim_name="Ramesh Kumar",
        complaint_reference=f"REF-{int(now.timestamp())}",
        amount_lost=10.0,
        currency="INR",
        incident_date=now,
        suspect_wallet=wallet_b,
        blockchain="Ethereum"
    )
    db.add(test_case)

    # Transactions:
    # Tx 1: A -> B (10.0 ETH)
    # Tx 2: B -> C (5.0 ETH) within 3 mins (Rapid + Splitting)
    # Tx 3: B -> D (4.9 ETH) within 4 mins
    # Tx 4: C -> E (4.8 ETH) [Multi-hop into known VASP]
    tx1 = Transaction(
        tx_hash=f"0xtx1_{int(now.timestamp())}",
        blockchain="Ethereum",
        chain_id=11155111,
        from_address=wallet_a,
        to_address=wallet_b,
        value_wei=str(int(10.0 * 1e18)),
        value_eth=10.0,
        block_number=11000001,
        block_timestamp=now,
        case_id=test_case_id
    )
    tx2 = Transaction(
        tx_hash=f"0xtx2_{int(now.timestamp())}",
        blockchain="Ethereum",
        chain_id=11155111,
        from_address=wallet_b,
        to_address=wallet_c,
        value_wei=str(int(5.0 * 1e18)),
        value_eth=5.0,
        block_number=11000002,
        block_timestamp=now + datetime.timedelta(seconds=180),
        case_id=test_case_id
    )
    tx3 = Transaction(
        tx_hash=f"0xtx3_{int(now.timestamp())}",
        blockchain="Ethereum",
        chain_id=11155111,
        from_address=wallet_b,
        to_address=wallet_d,
        value_wei=str(int(4.9 * 1e18)),
        value_eth=4.9,
        block_number=11000003,
        block_timestamp=now + datetime.timedelta(seconds=240),
        case_id=test_case_id
    )
    tx4 = Transaction(
        tx_hash=f"0xtx4_{int(now.timestamp())}",
        blockchain="Ethereum",
        chain_id=11155111,
        from_address=wallet_c,
        to_address=wallet_e,
        value_wei=str(int(4.8 * 1e18)),
        value_eth=4.8,
        block_number=11000004,
        block_timestamp=now + datetime.timedelta(seconds=600),
        case_id=test_case_id
    )
    db.add_all([tx1, tx2, tx3, tx4])
    db.commit()
    db.close()

    try:
        # 2. Test Phase 5 Pattern Detection on Suspect Wallet B
        pat_res = client.get(f"/analysis/wallet/{wallet_b}/patterns?max_hops=3")
        assert pat_res.status_code == 200
        pat_data = pat_res.json()
        assert pat_data["total_patterns_detected"] >= 1
        pattern_names = [p["pattern_name"] for p in pat_data["patterns"]]
        # Rapid transfer should be detected
        assert any("Rapid" in name for name in pattern_names)

        # 3. Test Phase 6 Risk Assessment on Wallet B
        risk_res = client.get(f"/risk/wallet/{wallet_b}?max_hops=3")
        assert risk_res.status_code == 200
        risk_data = risk_res.json()
        assert risk_data["risk_score"] > 0
        assert len(risk_data["contributions"]) >= 1

        # 4. Test Phase 7 Entity Resolution on Destination Wallet E
        ent_res = client.get(f"/entities/address/{wallet_e}")
        assert ent_res.status_code == 200
        ent_data = ent_res.json()
        assert ent_data["is_known"] is True
        assert ent_data["entity_type"] in ("EXCHANGE", "VASP")
        assert "Binance" in ent_data["entity_name"]

        # 5. Test Combined Investigation Endpoint for Wallet B
        inv_res = client.get(f"/investigation/wallet/{wallet_b}/analysis?case_id={test_case_id}&max_hops=3")
        assert inv_res.status_code == 200
        inv_data = inv_res.json()
        assert inv_data["wallet_address"] == wallet_b.lower()
        assert inv_data["risk_score"] > 0
        assert len(inv_data["patterns"]) >= 1
        assert len(inv_data["why_this_risk"]) >= 1
        assert "summary_verdict" in inv_data
        assert "disclaimer" in inv_data

        # 6. Test Combined Investigation Endpoint for Case
        case_inv_res = client.get(f"/cases/{test_case_id}/analysis?max_hops=3")
        assert case_inv_res.status_code == 200
        case_inv_data = case_inv_res.json()
        assert case_inv_data["case_id"] == test_case_id
        assert case_inv_data["risk_score"] > 0

    finally:
        # Clean up integration test records
        clean_db = SessionLocal()
        try:
            clean_db.query(AnalysisPattern).filter(AnalysisPattern.case_id == test_case_id).delete()
            clean_db.query(RiskAssessmentRecord).filter(RiskAssessmentRecord.case_id == test_case_id).delete()
            clean_db.query(Transaction).filter(Transaction.case_id == test_case_id).delete()
            clean_db.query(Case).filter(Case.case_id == test_case_id).delete()
            clean_db.commit()
        except Exception:
            clean_db.rollback()
        finally:
            clean_db.close()
