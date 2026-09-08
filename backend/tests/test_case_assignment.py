import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_case_lifecycle_and_assignment():
    unique_suffix = uuid.uuid4().hex[:6]
    
    # 1. Register a victim
    victim_data = {
        "username": f"victim_test_{unique_suffix}",
        "email": f"victim_{unique_suffix}@gmail.com",
        "password": "Password123!",
        "full_name": f"Victim User {unique_suffix}",
        "phone_number": f"98711{unique_suffix[:5]}",
        "role": "VICTIM"
    }
    reg_v = client.post("/api/auth/register", json=victim_data)
    assert reg_v.status_code == 200, reg_v.text
    victim_token = client.post("/api/auth/login", json={"username": victim_data["username"], "password": victim_data["password"]}).json()["access_token"]
    victim_headers = {"Authorization": f"Bearer {victim_token}"}

    # 2. Get available investigators
    avail_resp = client.get("/api/investigators/available")
    assert avail_resp.status_code == 200, avail_resp.text
    available_invs = avail_resp.json()
    assert len(available_invs) > 0
    assigned_inv = available_invs[0]
    inv_id = assigned_inv["id"]
    inv_username = assigned_inv["username"]

    # 3. Victim creates a dynamic complaint with wallet and amount
    suspect_addr = f"0x{uuid.uuid4().hex}"[:42]
    complaint_payload = {
        "title": f"Phishing Fraud Investigation {unique_suffix}",
        "description": "Defrauded via social engineering Telegram group.",
        "victim_name": victim_data["full_name"],
        "amount_lost": 250000.0,
        "currency": "INR",
        "suspect_wallet": suspect_addr,
        "transaction_hash": f"0x{uuid.uuid4().hex}{uuid.uuid4().hex}"[:66],
        "blockchain": "Ethereum Sepolia",
        "investigator_id": inv_id
    }
    create_resp = client.post("/api/cases", json=complaint_payload, headers=victim_headers)
    assert create_resp.status_code == 200, create_resp.text
    case_data = create_resp.json()
    case_id = case_data["case_id"]
    assert case_data["case_number"].startswith("CASE-")
    assert case_data["status"] == "ASSIGNED"
    assert case_data["suspect_wallet"].lower() == suspect_addr.lower()

    # 4. Login as assigned investigator and check notifications
    inv_token = client.post("/api/auth/login", json={"username": inv_username, "password": "password123"}).json().get("access_token")
    if not inv_token:
        # Fallback to default investigator
        inv_token = client.post("/api/auth/login", json={"username": "investigator", "password": "password123"}).json()["access_token"]
    inv_headers = {"Authorization": f"Bearer {inv_token}"}

    notif_count_resp = client.get("/api/notifications/unread-count", headers=inv_headers)
    assert notif_count_resp.status_code == 200

    notifs_resp = client.get("/api/notifications", headers=inv_headers)
    assert notifs_resp.status_code == 200
    notifs = notifs_resp.json()
    assert isinstance(notifs, list)

    # 5. Investigator accepts the case
    accept_resp = client.post(f"/api/cases/{case_id}/accept", headers=inv_headers)
    assert accept_resp.status_code == 200, accept_resp.text
    assert accept_resp.json()["status"] == "ACCEPTED"

    # 6. Investigator starts investigation
    start_resp = client.post(f"/api/cases/{case_id}/start-investigation", headers=inv_headers)
    assert start_resp.status_code == 200, start_resp.text
    assert start_resp.json()["status"] == "UNDER_INVESTIGATION"

    # 7. Check recommendations endpoint
    recs_resp = client.get(f"/api/cases/{case_id}/recommendations", headers=inv_headers)
    assert recs_resp.status_code == 200, recs_resp.text
    recs = recs_resp.json()
    assert recs["case_id"] == case_id
    assert recs["total_recommendations"] >= 1

    # 8. Check NCRP & SAHYOG export formats
    ncrp_resp = client.get(f"/api/cases/{case_id}/export/ncrp", headers=inv_headers)
    assert ncrp_resp.status_code == 200, ncrp_resp.text
    ncrp_data = ncrp_resp.json()
    assert ncrp_data["schema_version"] == "NCRP-CYBERFRAUD-2.1"
    assert ncrp_data["acknowledgement_number"] == case_data["case_number"]

    sahyog_resp = client.get(f"/api/cases/{case_id}/export/sahyog", headers=inv_headers)
    assert sahyog_resp.status_code == 200, sahyog_resp.text
    sahyog_data = sahyog_resp.json()
    assert sahyog_data["sahyog_version"] == "SAHYOG-I4C-V1"
    assert sahyog_data["case_identifier"] == case_data["case_number"]

def test_complaint_without_suspect_wallet():
    """Test complainant reporting crypto scam with transaction hash only or bank memo only"""
    unique_suffix = uuid.uuid4().hex[:6]
    victim_data = {
        "username": f"victim_nowallet_{unique_suffix}",
        "email": f"victim_nw_{unique_suffix}@gmail.com",
        "password": "Password123!",
        "full_name": f"Victim Bank Transfer {unique_suffix}",
        "role": "VICTIM"
    }
    client.post("/api/auth/register", json=victim_data)
    victim_token = client.post("/api/auth/login", json={"username": victim_data["username"], "password": victim_data["password"]}).json()["access_token"]
    victim_headers = {"Authorization": f"Bearer {victim_token}"}

    # Case with transaction hash only (no wallet known by victim)
    tx_hash = f"0x{uuid.uuid4().hex}{uuid.uuid4().hex}"[:66]
    case_payload = {
        "title": "Crypto Scam via Fraudulent Gateway",
        "description": "Victim has only the tx hash from the payment gateway",
        "amount_lost": 75000.0,
        "currency": "INR",
        "transaction_hash": tx_hash,
        "suspect_wallet": None
    }
    create_resp = client.post("/api/cases", json=case_payload, headers=victim_headers)
    assert create_resp.status_code == 200, create_resp.text
    data = create_resp.json()
    assert data["suspect_wallet"] is None
    assert data["transaction_hash"] == tx_hash
