import pytest
import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database.database import SessionLocal
from app.database.models import Case, Evidence, InvestigationTimeline

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

def test_phase9_case_workspace_timeline_and_evidence():
    db = SessionLocal()
    token = get_auth_token("investigator")
    headers = {"Authorization": f"Bearer {token}"}

    case_id = f"CASE-P9-{int(datetime.datetime.utcnow().timestamp())}"
    wallet = "0x7777777777777777777777777777777777777777"

    case = Case(
        case_id=case_id,
        victim_name="Workspace Subject",
        complaint_reference=f"REF-P9-{int(datetime.datetime.utcnow().timestamp())}",
        amount_lost=5.0,
        currency="ETH",
        incident_date=datetime.datetime.utcnow(),
        suspect_wallet=wallet,
        blockchain="Ethereum",
        status="OPEN"
    )
    db.add(case)
    db.commit()

    try:
        # 1. Test case workspace overview
        res = client.get(f"/api/cases/{case_id}/workspace", headers=headers)
        assert res.status_code == 200, res.text
        ws = res.json()
        assert ws["case_id"] == case_id
        assert ws["suspect_wallet"] == wallet
        assert "timeline" in ws
        assert "evidence_count" in ws

        # 2. Test add evidence item with integrity hash calculation
        ev_payload = {
            "case_id": case_id,
            "blockchain": "Ethereum",
            "wallet": wallet,
            "transaction_hash": f"0xevtx{int(datetime.datetime.utcnow().timestamp())}",
            "block_number": 500,
            "from_address": wallet,
            "to_address": "0x6666666666666666666666666666666666666666",
            "amount": 2.5,
            "tag": "SUSPICIOUS_TRANSFER",
            "investigator_notes": "Preserved for court presentation"
        }
        ev_res = client.post(f"/api/cases/{case_id}/evidence", headers=headers, json=ev_payload)
        assert ev_res.status_code == 200, ev_res.text
        ev_data = ev_res.json()
        assert ev_data["evidence_id"].startswith("EV-")
        assert len(ev_data["integrity_hash"]) == 64  # SHA-256 hex digest

        # 3. Test retrieve evidence locker
        ev_list = client.get(f"/api/cases/{case_id}/evidence", headers=headers)
        assert ev_list.status_code == 200
        assert len(ev_list.json()) >= 1

        # 4. Test timeline events
        tl_res = client.get(f"/api/cases/{case_id}/timeline", headers=headers)
        assert tl_res.status_code == 200
        assert len(tl_res.json()) >= 1  # Evidence added created a timeline event!

        # 5. Test status update with RBAC (Investigator transitioning to UNDER_INVESTIGATION)
        status_res = client.patch(
            f"/api/cases/{case_id}/status?new_status=UNDER_INVESTIGATION",
            headers=headers
        )
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "UNDER_INVESTIGATION"

    finally:
        db.query(Evidence).filter(Evidence.case_id == case_id).delete()
        db.query(InvestigationTimeline).filter(InvestigationTimeline.case_id == case_id).delete()
        db.query(Case).filter(Case.case_id == case_id).delete()
        db.commit()
        db.close()
