import pytest
import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database.database import SessionLocal
from app.database.models import Case, Transaction, PriorityItem, AddressLabel, EntityType, ConfidenceLevel

client = TestClient(app)

def get_auth_token(role="investigator"):
    creds = {
        "investigator": ("investigator", "password123"),
        "supervisor": ("supervisor", "password123"),
        "admin": ("admin", "password123")
    }
    username, password = creds.get(role, creds["investigator"])
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    return res.json().get("access_token")

def test_phase8_priority_calculation_and_queue():
    db = SessionLocal()
    token = get_auth_token("investigator")
    headers = {"Authorization": f"Bearer {token}"}

    case_id = f"CASE-P8-{int(datetime.datetime.utcnow().timestamp())}"
    suspect_wallet = "0x8888888888888888888888888888888888888888"
    counterparty = "0x9999999999999999999999999999999999999999"

    case = Case(
        case_id=case_id,
        victim_name="Priority Test Subject",
        complaint_reference=f"REF-P8-{int(datetime.datetime.utcnow().timestamp())}",
        amount_lost=25.0,
        currency="ETH",
        incident_date=datetime.datetime.utcnow(),
        suspect_wallet=suspect_wallet,
        blockchain="Ethereum",
        priority="HIGH"
    )
    db.add(case)

    # Insert transactions
    t0 = datetime.datetime.utcnow()
    tx = Transaction(
        transaction_hash=f"0xp8tx01{int(t0.timestamp())}",
        blockchain="Ethereum",
        chain_id=11155111,
        case_id=case_id,
        from_address=suspect_wallet,
        to_address=counterparty,
        amount_native=15.5,
        timestamp=t0,
        block_number=100
    )
    db.add(tx)
    db.commit()

    try:
        # 1. Test prioritize case leads endpoint
        res = client.get(f"/api/priority/case/{case_id}", headers=headers)
        assert res.status_code == 200, res.text
        leads = res.json()
        assert len(leads) >= 1
        top_lead = leads[0]
        assert top_lead["priority_category"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert 0.0 <= top_lead["priority_score"] <= 100.0
        assert "reasons" in top_lead
        assert len(top_lead["reasons"]) > 0

        # 2. Test global priority queue
        q_res = client.get("/api/priority/queue", headers=headers)
        assert q_res.status_code == 200
        q_data = q_res.json()
        assert "total_leads" in q_data
        assert "queue" in q_data

        # 3. Test lead review endpoint
        lead_id = top_lead["id"]
        rev_res = client.post(
            f"/api/priority/{lead_id}/review",
            headers=headers,
            json={"status": "IMPORTANT", "notes": "High priority exit node flagged for review"}
        )
        assert rev_res.status_code == 200
        rev_lead = rev_res.json()
        assert rev_lead["status"] == "IMPORTANT"

        # 4. Test lead note addition
        note_res = client.post(
            f"/api/priority/{lead_id}/note",
            headers=headers,
            json={"note": "Subpoena notice prepared for exchange counterparty."}
        )
        assert note_res.status_code == 200

        # 5. Test lead assignment (Supervisor role required)
        sup_token = get_auth_token("supervisor")
        sup_headers = {"Authorization": f"Bearer {sup_token}"}
        assign_res = client.post(
            f"/api/priority/{lead_id}/assign",
            headers=sup_headers,
            json={"assigned_to": "investigator"}
        )
        assert assign_res.status_code == 200
        assert assign_res.json()["assigned_to"] == "investigator"

    finally:
        db.query(PriorityItem).filter(PriorityItem.case_id == case_id).delete()
        db.query(Transaction).filter(Transaction.case_id == case_id).delete()
        db.query(Case).filter(Case.case_id == case_id).delete()
        db.commit()
        db.close()
