import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database.models import Monitoring, Alert, Transaction, AuditLog
from app.database.schemas import MonitoringCreate

class MonitoringService:
    @staticmethod
    def add_to_watchlist(
        db: Session,
        req: MonitoringCreate,
        username: str
    ) -> Monitoring:
        existing = db.query(Monitoring).filter(
            Monitoring.case_id == req.case_id,
            Monitoring.wallet_address == req.wallet_address
        ).first()

        if existing:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
            return existing

        item = Monitoring(
            case_id=req.case_id,
            wallet_address=req.wallet_address,
            blockchain=req.blockchain,
            label=req.label,
            is_active=True
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        log = AuditLog(
            username=username,
            action="WALLET_MONITORED",
            case_id=req.case_id,
            metadata_json={"wallet_address": req.wallet_address, "blockchain": req.blockchain}
        )
        db.add(log)
        db.commit()
        return item

    @staticmethod
    def simulate_new_activity_and_alert(
        db: Session,
        monitoring_id: int,
        tx_hash: str,
        amount: float,
        recipient_label: str = "Binance Hot Wallet (VASP)"
    ) -> Alert:
        """
        Triggered when a monitored wallet registers fresh transaction activity.
        Generates a high-priority alert for the investigator dashboard.
        """
        m = db.query(Monitoring).filter(Monitoring.id == monitoring_id).first()
        if not m:
            raise ValueError("Monitoring entry not found")

        alert = Alert(
            monitoring_id=m.id,
            wallet_address=m.wallet_address,
            tx_hash=tx_hash,
            risk_level="CRITICAL",
            reason=(
                f"Fresh transaction detected from monitored wallet {m.wallet_address[:10]}... "
                f"Value: {amount:.4f} ETH routed to {recipient_label}."
            ),
            timestamp=datetime.datetime.utcnow(),
            is_read=False
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def get_case_monitoring(db: Session, case_id: str) -> List[Monitoring]:
        return db.query(Monitoring).filter(Monitoring.case_id == case_id).all()

    @staticmethod
    def get_all_alerts(db: Session, unread_only: bool = False, case_id: Optional[str] = None) -> List[Alert]:
        q = db.query(Alert)
        if case_id:
            q = q.join(Monitoring, Alert.monitoring_id == Monitoring.id).filter(Monitoring.case_id == case_id)
        if unread_only:
            q = q.filter(Alert.is_read == False)
        return q.order_by(Alert.timestamp.desc()).all()

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: int, username: str) -> Alert:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.is_read = True
        db.commit()
        db.refresh(alert)

        # Audit log
        log = AuditLog(
            username=username,
            action="ALERT_ACKNOWLEDGED",
            case_id=alert.monitoring.case_id if alert.monitoring else None,
            metadata_json={"alert_id": alert_id, "wallet": alert.wallet_address, "tx_hash": alert.tx_hash}
        )
        db.add(log)
        db.commit()
        return alert

    @staticmethod
    def update_alert_status(db: Session, alert_id: int, is_read: bool, username: str) -> Alert:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.is_read = is_read
        db.commit()
        db.refresh(alert)

        log = AuditLog(
            username=username,
            action="ALERT_STATUS_UPDATED",
            case_id=alert.monitoring.case_id if alert.monitoring else None,
            metadata_json={"alert_id": alert_id, "is_read": is_read}
        )
        db.add(log)
        db.commit()
        return alert

    @staticmethod
    def create_alert_rule(db: Session, rule_data: Any, username: str):
        from app.database.models import AlertRule
        rule = AlertRule(
            case_id=rule_data.case_id,
            rule_name=rule_data.rule_name,
            rule_type=rule_data.rule_type,
            threshold_value=rule_data.threshold_value,
            is_active=rule_data.is_active
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)

        log = AuditLog(
            username=username,
            action="ALERT_RULE_CREATED",
            case_id=rule_data.case_id,
            metadata_json={"rule_id": rule.id, "rule_name": rule.rule_name, "rule_type": rule.rule_type}
        )
        db.add(log)
        db.commit()
        return rule

    @staticmethod
    def get_alert_rules(db: Session, case_id: Optional[str] = None):
        from app.database.models import AlertRule
        q = db.query(AlertRule)
        if case_id:
            q = q.filter((AlertRule.case_id == case_id) | (AlertRule.case_id == None))
        return q.order_by(AlertRule.created_at.desc()).all()

    @staticmethod
    def delete_alert_rule(db: Session, rule_id: int, username: str) -> bool:
        from app.database.models import AlertRule
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")

        case_id = rule.case_id
        rule_name = rule.rule_name
        db.delete(rule)
        db.commit()

        log = AuditLog(
            username=username,
            action="ALERT_RULE_DELETED",
            case_id=case_id,
            metadata_json={"rule_id": rule_id, "rule_name": rule_name}
        )
        db.add(log)
        db.commit()
        return True

