import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.database import SessionLocal
from app.database.models import AddressLabel, EntityType
from app.entities.resolver import EntityResolver
from app.entities.service import EntityService

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def seed_demo_data():
    db = SessionLocal()
    EntityService.seed_demo_intel(db)
    db.close()

def test_known_exchange_resolution():
    binance_addr = "0x28C6c06298d514Db089934071355E5743bf21d60"
    res = client.get(f"/entities/address/{binance_addr}")
    assert res.status_code == 200
    data = res.json()
    assert data["is_known"] is True
    assert data["entity_type"] in ("EXCHANGE", "VASP")
    assert "Binance" in data["entity_name"]
    assert data["confidence"] == "HIGH"

def test_unknown_address_remains_unknown():
    unlabeled_addr = "0x9999999999999999999999999999999999999999"
    res = client.get(f"/entities/address/{unlabeled_addr}")
    assert res.status_code == 200
    data = res.json()
    assert data["is_known"] is False
    assert data["entity_type"] == "UNKNOWN"
    assert data["entity_name"] is None
    assert data["verified"] is False
    assert data["confidence"] == "LOW"

def test_create_label_and_duplicate_prevention():
    test_addr = "0x1234567890123456789012345678901234567890"
    payload = {
        "address": test_addr,
        "blockchain": "Ethereum",
        "chain_id": 11155111,
        "entity_type": "VASP",
        "entity_name": "Test VASP",
        "label": "Test VASP Deposit Hub",
        "confidence": "HIGH",
        "verified": True
    }

    # First creation
    res1 = client.post("/entities/labels", json=payload)
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["entity_name"] == "Test VASP"

    # Second call should update instead of creating duplicate
    payload["entity_name"] = "Updated Test VASP"
    res2 = client.post("/entities/labels", json=payload)
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["entity_name"] == "Updated Test VASP"
    assert d2["id"] == d1["id"]

def test_search_entities():
    res = client.get("/entities/search?q=Binance")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    assert any("Binance" in item["entity_name"] for item in items)

def test_dataset_import():
    import time
    dynamic_addr = f"0x{'5' * 34}{int(time.time()) % 1000000:06d}"
    payload = {
        "dataset_name": "UnitTest Dataset",
        "labels": [
            {
                "address": dynamic_addr,
                "blockchain": "Ethereum",
                "chain_id": 11155111,
                "entity_type": "DEX",
                "entity_name": "Imported DEX",
                "confidence": "HIGH",
                "verified": True
            },
            {
                "address": "invalid_address_format",
                "blockchain": "Ethereum",
                "chain_id": 11155111,
                "entity_type": "EXCHANGE",
                "entity_name": "Bad Address"
            }
        ]
    }

    res = client.post("/entities/import", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["imported_count"] >= 1
    assert data["failed_count"] >= 1
    assert len(data["errors"]) >= 1

def test_invalid_address_validation():
    res = client.get("/entities/address/not_an_address")
    assert res.status_code == 400
