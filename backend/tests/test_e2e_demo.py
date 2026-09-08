import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_and_status():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["mode"] in ("DEMO_MODE", "LIVE_MODE")

def test_auth_and_login():
    # Login as investigator
    res = client.post("/api/auth/login", json={
        "username": "investigator",
        "password": "password123"
    })
    assert res.status_code == 200
    token_data = res.json()
    assert "access_token" in token_data
    assert token_data["user"]["role"] == "INVESTIGATOR"

def test_sih_hackathon_demo_flow():
    # 1. Login
    login_res = client.post("/api/auth/login", json={
        "username": "investigator",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Seed / Get Demo Case
    seed_res = client.post("/api/cases/seed-demo", headers=headers)
    assert seed_res.status_code == 200
    case_data = seed_res.json()
    case_id = case_data["case_id"]
    assert case_data["victim_name"] == "Rahul Sharma"
    assert case_data["amount_lost"] == 500000.0

    # 3. Get Money Trail
    trail_res = client.get(f"/api/analysis/trail/{case_id}", headers=headers)
    assert trail_res.status_code == 200
    trail_data = trail_res.json()
    assert trail_data["verified_paths_count"] >= 1
    primary_path = trail_data["paths_to_vasp"][0]
    assert "Binance" in primary_path["destination_vasp"]
    assert primary_path["hops"] >= 3

    # 4. Get Graph
    graph_res = client.get(f"/api/analysis/graph/{case_id}?hops=4", headers=headers)
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert graph_data["node_count"] >= 5
    assert graph_data["edge_count"] >= 5

    # 5. Query Copilot
    copilot_res = client.post("/api/copilot/query", json={
        "case_id": case_id,
        "question": "Where did the victim's money go?"
    }, headers=headers)
    assert copilot_res.status_code == 200
    copilot_data = copilot_res.json()
    assert "Binance" in copilot_data["answer"]
    assert len(copilot_data["grounded_evidence"]) > 0

    # 6. Save Evidence
    ev_res = client.post("/api/evidence", json={
        "case_id": case_id,
        "blockchain": "Ethereum",
        "wallet": "0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97",
        "transaction_hash": "0x012345678abcdef9012345678abcdef9012345678abcdef07",
        "from_address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "to_address": "0x28C6c06298d514Db089934071355E5743bf21d60",
        "amount": 1.15,
        "tag": "PRIMARY_FLOW",
        "investigator_notes": "Terminal deposit into Binance Hot Wallet verified."
    }, headers=headers)
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert "integrity_hash" in ev_data
    assert len(ev_data["integrity_hash"]) == 64 # SHA-256

    # 7. Generate Report
    rep_res = client.post("/api/reports/generate", json={
        "case_id": case_id,
        "title": "Forensic Crypto Investigation Report - Rahul Sharma Case"
    }, headers=headers)
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    report_id = rep_data["report_id"]
    assert rep_data["status"] == "PENDING_REVIEW"

    # 8. Supervisor Review & Approval
    sup_login = client.post("/api/auth/login", json={
        "username": "supervisor",
        "password": "password123"
    })
    sup_token = sup_login.json()["access_token"]
    sup_headers = {"Authorization": f"Bearer {sup_token}"}

    review_res = client.patch(f"/api/reports/{report_id}/review", json={
        "status": "APPROVED",
        "supervisor_comments": "Verified against Binance exchange records. Proceed with formal notice under Section 91 CrPC."
    }, headers=sup_headers)
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "APPROVED"
