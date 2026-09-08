import pytest
import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database.database import SessionLocal
from app.database.models import Case, Transaction, CopilotMessage

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

def test_phase10_investigator_copilot():
    db = SessionLocal()
    token = get_auth_token("investigator")
    headers = {"Authorization": f"Bearer {token}"}

    case_id = f"CASE-P10-{int(datetime.datetime.utcnow().timestamp())}"
    wallet = "0x5555555555555555555555555555555555555555"

    case = Case(
        case_id=case_id,
        victim_name="Copilot Test Subject",
        complaint_reference=f"REF-P10-{int(datetime.datetime.utcnow().timestamp())}",
        amount_lost=3.0,
        currency="ETH",
        incident_date=datetime.datetime.utcnow(),
        suspect_wallet=wallet,
        blockchain="Ethereum"
    )
    db.add(case)
    db.commit()

    try:
        # 1. Test case-specific prompt suggestions
        sug_res = client.get(f"/api/copilot/case/{case_id}/suggestions", headers=headers)
        assert sug_res.status_code == 200
        suggestions = sug_res.json()
        assert len(suggestions) >= 3

        # 2. Test grounded query regarding suspect wallet
        ask_res = client.post(
            f"/api/copilot/case/{case_id}/ask",
            headers=headers,
            json={"question": "What is the suspect wallet address and status of this case?"}
        )
        assert ask_res.status_code == 200, ask_res.text
        ans = ask_res.json()
        assert wallet.lower() in ans["answer"].lower() or wallet[:10].lower() in ans["answer"].lower()
        assert ans["confidence"] in ["HIGH", "MEDIUM", "LOW"]

        # 3. Test anti-hallucination constraint when no transaction data exists
        unrelated_res = client.post(
            f"/api/copilot/case/{case_id}/ask",
            headers=headers,
            json={"question": "Did this suspect use Tornado Cash or a mixer?"}
        )
        assert unrelated_res.status_code == 200
        unrelated_ans = unrelated_res.json()["answer"]
        # Grounded copilot must not fabricate facts when no transactions are ingested
        assert "insufficient" in unrelated_ans.lower() or "no " in unrelated_ans.lower() or "not detected" in unrelated_ans.lower()

        # 4. Test global chat endpoint
        chat_res = client.post(
            "/api/copilot/chat",
            headers=headers,
            json={"message": "Explain how multi-hop peeling chains operate."}
        )
        assert chat_res.status_code == 200
        chat_data = chat_res.json()
        assert "answer" in chat_data

    finally:
        db.query(CopilotMessage).filter(CopilotMessage.case_id == case_id).delete()
        db.query(Case).filter(Case.case_id == case_id).delete()
        db.commit()
        db.close()
