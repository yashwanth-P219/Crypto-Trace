import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.database import SessionLocal
from app.database.models import CrossChainLink

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

def test_phase12_multichain_and_cross_chain():
    db = SessionLocal()
    token = get_auth_token("investigator")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List supported chains
    chains_res = client.get("/chains", headers=headers)
    assert chains_res.status_code == 200, chains_res.text
    chains = chains_res.json()
    chain_ids = [c["chain_id"] for c in chains]
    assert 11155111 in chain_ids  # Sepolia
    assert 1 in chain_ids         # Mainnet
    assert 137 in chain_ids       # Polygon
    assert 56 in chain_ids        # BNB

    # 2. Get specific chain details
    sep_res = client.get("/chains/11155111", headers=headers)
    assert sep_res.status_code == 200
    assert sep_res.json()["name"] == "Ethereum Sepolia"

    # 3. Reject unsupported chain
    bad_res = client.get("/chains/99999", headers=headers)
    assert bad_res.status_code == 400
    assert "unsupported" in bad_res.json()["detail"].lower()

    # 4. Query multi-chain wallet
    wallet = "0x28c6c06298d514db089934071355e5743bf21d60"
    w_res = client.get(f"/chains/11155111/wallet/{wallet}", headers=headers)
    assert w_res.status_code == 200
    assert w_res.json()["chain_id"] == 11155111

    # 5. Query known bridges
    br_res = client.get("/cross-chain/bridges", headers=headers)
    assert br_res.status_code == 200
    bridges = br_res.json()
    assert len(bridges) >= 3

    # 6. Detect cross-chain flow on a known bridge address
    polygon_bridge = "0xa0c68c638235ee32657e8f720a23cec1bfc77c77"
    det_res = client.get(f"/cross-chain/wallet/{polygon_bridge}", headers=headers)
    assert det_res.status_code == 200
    det_data = det_res.json()
    assert det_data["is_known_bridge"] is True
    assert "Polygon" in det_data["bridge_metadata"]["name"]

    # 7. Record cross-chain asset transition
    link_payload = {
        "source_chain_id": 1,
        "destination_chain_id": 137,
        "source_tx_hash": "0xbridge0000000000000000000000000000000000000000000000000000000001",
        "bridge_contract": polygon_bridge,
        "bridge_name": "Polygon PoS Bridge",
        "amount": 4.5
    }
    rec_res = client.post("/cross-chain/record-link", headers=headers, json=link_payload)
    assert rec_res.status_code == 200, rec_res.text
    link_id = rec_res.json()["id"]

    # 8. List cross-chain links
    links_res = client.get("/cross-chain/links", headers=headers)
    assert links_res.status_code == 200
    assert any(l["id"] == link_id for l in links_res.json())

    # Cleanup
    db.query(CrossChainLink).filter(CrossChainLink.id == link_id).delete()
    db.commit()
    db.close()
