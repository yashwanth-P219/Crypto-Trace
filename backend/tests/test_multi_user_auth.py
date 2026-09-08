import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_victim_registration_and_login():
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"victim_{unique_suffix}"
    email = f"victim_{unique_suffix}@example.com"
    phone = f"98765{unique_suffix[:5]}"
    password = "VictimPassword123!"

    # 1. Register as VICTIM
    reg_payload = {
        "username": username,
        "email": email,
        "password": password,
        "full_name": f"Test Complainant {unique_suffix}",
        "phone_number": phone,
        "role": "VICTIM"
    }
    response = client.post("/api/auth/register", json=reg_payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == username
    assert data["role"] == "VICTIM"

    # 2. Login using username
    login_resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login_resp.status_code == 200, login_resp.text
    assert "access_token" in login_resp.json()

    # 3. Login using email
    login_email_resp = client.post("/api/auth/login", json={"username": email, "password": password})
    assert login_email_resp.status_code == 200, login_email_resp.text
    assert "access_token" in login_email_resp.json()

    # 4. Login using phone
    login_phone_resp = client.post("/api/auth/login", json={"username": phone, "password": password})
    assert login_phone_resp.status_code == 200, login_phone_resp.text
    assert "access_token" in login_phone_resp.json()

def test_investigator_registration_and_admin_approval():
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"inv_{unique_suffix}"
    email = f"inv_{unique_suffix}@police.gov.in"
    phone = f"91111{unique_suffix[:5]}"
    password = "InvSecurePassword123!"

    # 1. Register as INVESTIGATOR
    reg_payload = {
        "username": username,
        "email": email,
        "password": password,
        "full_name": f"Officer {unique_suffix}",
        "phone_number": phone,
        "role": "INVESTIGATOR",
        "badge_number": f"CYBER-{unique_suffix.upper()}",
        "department": "Cyber Crime Branch",
        "jurisdiction": "Central Division"
    }
    reg_resp = client.post("/api/auth/register", json=reg_payload)
    assert reg_resp.status_code == 200, reg_resp.text
    user_id = reg_resp.json()["id"]

    # 2. Verify investigator starts with PENDING status and is NOT yet available
    avail_resp = client.get("/api/investigators/available")
    assert avail_resp.status_code == 200
    available_invs = avail_resp.json()
    assert not any(inv["id"] == user_id for inv in available_invs)

    # 3. Admin login
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "password123"})
    assert admin_login.status_code == 200, admin_login.text
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 4. Check admin list contains the pending investigator
    admin_list_resp = client.get("/api/investigators/admin/list?status=PENDING", headers=admin_headers)
    assert admin_list_resp.status_code == 200
    pending_list = admin_list_resp.json()
    assert any(p["user_id"] == user_id for p in pending_list)

    # 5. Admin approves investigator
    approve_resp = client.post(
        f"/api/investigators/admin/{user_id}/approve",
        json={"reason": "Credentials verified against police registry"},
        headers=admin_headers
    )
    assert approve_resp.status_code == 200, approve_resp.text
    assert approve_resp.json()["approval_status"] == "APPROVED"

    # 6. Verify now listed in available investigators
    avail_resp_2 = client.get("/api/investigators/available")
    assert avail_resp_2.status_code == 200
    assert any(inv["id"] == user_id for inv in avail_resp_2.json())

    # 7. Investigator updates availability to BUSY
    inv_login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert inv_login.status_code == 200
    inv_token = inv_login.json()["access_token"]
    inv_headers = {"Authorization": f"Bearer {inv_token}"}

    update_avail = client.patch(
        "/api/investigators/availability",
        json={"availability_status": "BUSY", "max_active_cases": 8},
        headers=inv_headers
    )
    assert update_avail.status_code == 200
    assert update_avail.json()["availability_status"] == "BUSY"

    # 8. Should no longer be listed as available since status is BUSY
    avail_resp_3 = client.get("/api/investigators/available")
    assert not any(inv["id"] == user_id for inv in avail_resp_3.json())


def test_general_user_cannot_access_investigator_approval_controls():
    unique_suffix = uuid.uuid4().hex[:6]
    reg_resp = client.post("/api/auth/register", json={
        "username": f"victim_admin_{unique_suffix}",
        "email": f"victim_admin_{unique_suffix}@example.com",
        "password": "VictimPassword123!",
        "full_name": "General User",
        "role": "VICTIM"
    })
    assert reg_resp.status_code == 200, reg_resp.text

    login_resp = client.post("/api/auth/login", json={
        "username": f"victim_admin_{unique_suffix}",
        "password": "VictimPassword123!"
    })
    assert login_resp.status_code == 200, login_resp.text
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    list_resp = client.get("/api/investigators/admin/list", headers=headers)
    assert list_resp.status_code == 403
