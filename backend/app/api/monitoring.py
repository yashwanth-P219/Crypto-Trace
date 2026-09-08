from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User, UserRole
from app.database.schemas import (
    MonitoringCreate, MonitoringResponse, AlertResponse,
    AlertStatusUpdate, AlertRuleCreate, AlertRuleResponse
)
from app.api.auth import get_current_user, require_roles
from app.services.monitoring_service import MonitoringService

router = APIRouter(prefix="/monitoring", tags=["Wallet Watchlist & Alerts"])

@router.post("", response_model=MonitoringResponse)
def add_monitored_wallet(
    req: MonitoringCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INVESTIGATOR, UserRole.SUPERVISOR]))
):
    return MonitoringService.add_to_watchlist(db, req, current_user.username)

@router.get("/case/{case_id}", response_model=List[MonitoringResponse])
def get_case_monitored_wallets(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return MonitoringService.get_case_monitoring(db, case_id)

@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(
    unread_only: bool = False,
    case_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return MonitoringService.get_all_alerts(db, unread_only=unread_only, case_id=case_id)

@router.patch("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INVESTIGATOR, UserRole.SUPERVISOR, UserRole.ADMINISTRATOR]))
):
    try:
        return MonitoringService.acknowledge_alert(db, alert_id, current_user.username)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/alerts/{alert_id}/status", response_model=AlertResponse)
@router.post("/alerts/{alert_id}/status", response_model=AlertResponse)
def update_alert_status(
    alert_id: int,
    req: AlertStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INVESTIGATOR, UserRole.SUPERVISOR, UserRole.ADMINISTRATOR]))
):
    try:
        return MonitoringService.update_alert_status(db, alert_id, req.is_read, current_user.username)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/rules", response_model=List[AlertRuleResponse])
@router.get("/rules/{case_id}", response_model=List[AlertRuleResponse])
def get_alert_rules(
    case_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return MonitoringService.get_alert_rules(db, case_id)

@router.post("/rules", response_model=AlertRuleResponse)
def create_alert_rule(
    req: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INVESTIGATOR, UserRole.SUPERVISOR]))
):
    return MonitoringService.create_alert_rule(db, req, current_user.username)

@router.delete("/rules/{rule_id}")
def delete_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INVESTIGATOR, UserRole.SUPERVISOR]))
):
    try:
        MonitoringService.delete_alert_rule(db, rule_id, current_user.username)
        return {"status": "deleted", "rule_id": rule_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/simulate-alert/{monitoring_id}", response_model=AlertResponse)
def simulate_wallet_alert(
    monitoring_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INVESTIGATOR, UserRole.SUPERVISOR, UserRole.ADMINISTRATOR]))
):
    """Simulates real-time detection of high-risk activity on monitored address"""
    import uuid
    dummy_tx = f"0x{uuid.uuid4().hex}"
    return MonitoringService.simulate_new_activity_and_alert(
        db=db,
        monitoring_id=monitoring_id,
        tx_hash=dummy_tx,
        amount=1.15,
        recipient_label="Binance 14 (Hot Wallet)"
    )

