import pytest
import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database.database import SessionLocal
from app.database.models import Case, Monitoring, Alert, AlertRule, Report, AuditLog

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

def test_phase11_monitoring_alerts_reports_audit():
    db = SessionLocal()
    token = get_auth_token("investigator")
    headers = {"Authorization": f"Bearer {token}"}

    case_id = f"CASE-P11-{int(datetime.datetime.utcnow().timestamp())}"
    wallet = "0x4444444444444444444444444444444444444444"

    case = Case(
        case_id=case_id,
        victim_name="Monitoring Subject",
        complaint_reference=f"REF-P11-{int(datetime.datetime.utcnow().timestamp())}",
        amount_lost=8.0,
        currency="ETH",
        incident_date=datetime.datetime.utcnow(),
        suspect_wallet=wallet,
        blockchain="Ethereum"
    )
    db.add(case)
    db.commit()

    try:
        # 1. Add wallet to monitoring
        mon_res = client.post(
            "/api/monitoring",
            headers=headers,
            json={"case_id": case_id, "wallet_address": wallet, "blockchain": "Ethereum", "label": "Suspect Cold Storage"}
        )
        assert mon_res.status_code == 200, mon_res.text
        mon_id = mon_res.json()["id"]

        # 2. Simulate alert
        sim_res = client.post(f"/api/monitoring/simulate-alert/{mon_id}", headers=headers)
        assert sim_res.status_code == 200
        alert_id = sim_res.json()["id"]

        # 3. Acknowledge alert
        ack_res = client.patch(f"/api/monitoring/alerts/{alert_id}/acknowledge", headers=headers)
        assert ack_res.status_code == 200
        assert ack_res.json()["is_read"] is True

        # 4. Create and list alert rules
        rule_res = client.post(
            "/api/monitoring/rules",
            headers=headers,
            json={
                "case_id": case_id,
                "rule_name": "High Value Transfer Rule",
                "rule_type": "LARGE_TRANSACTION",
                "threshold_value": 5.0,
                "is_active": True
            }
        )
        assert rule_res.status_code == 200
        rule_id = rule_res.json()["id"]

        rules_list = client.get(f"/api/monitoring/rules/{case_id}", headers=headers)
        assert rules_list.status_code == 200
        assert any(r["id"] == rule_id for r in rules_list.json())

        # Delete rule
        del_rule = client.delete(f"/api/monitoring/rules/{rule_id}", headers=headers)
        assert del_rule.status_code == 200

        # 5. Generate forensic investigation report
        rep_res = client.post(
            "/api/reports/generate",
            headers=headers,
            json={"case_id": case_id, "title": "Forensic Inspection Report P11"}
        )
        assert rep_res.status_code == 200, rep_res.text
        rep_data = rep_res.json()
        report_id = rep_data["report_id"]
        assert "integrity_hash_sha256" in rep_data["content_json"]["report_metadata"]

        # 6. Test PDF export
        pdf_res = client.get(f"/api/reports/{report_id}/pdf", headers=headers)
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert len(pdf_res.content) > 1000  # Non-trivial PDF generated!

        # 7. Test JSON and CSV exports
        json_res = client.get(f"/api/reports/{report_id}/json", headers=headers)
        assert json_res.status_code == 200
        assert "application/json" in json_res.headers["content-type"]

        csv_res = client.get(f"/api/reports/{report_id}/csv", headers=headers)
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res.headers["content-type"]
        assert "REPORT_ID" in csv_res.text

        # 8. Test audit logs and cryptographic audit verification
        audit_res = client.get(f"/api/audit?case_id={case_id}", headers=headers)
        assert audit_res.status_code == 200
        assert len(audit_res.json()) >= 1

        verify_res = client.get(f"/api/audit/verify/{case_id}", headers=headers)
        assert verify_res.status_code == 200
        assert verify_res.json()["status"] == "VERIFIED_TAMPER_FREE"
        assert len(verify_res.json()["audit_chain_sha256"]) == 64

    finally:
        db.query(Alert).filter(Alert.wallet_address == wallet).delete()
        db.query(Monitoring).filter(Monitoring.case_id == case_id).delete()
        db.query(AlertRule).filter(AlertRule.case_id == case_id).delete()
        db.query(Report).filter(Report.case_id == case_id).delete()
        db.query(AuditLog).filter(AuditLog.case_id == case_id).delete()
        db.query(Case).filter(Case.case_id == case_id).delete()
        db.commit()
        db.close()
