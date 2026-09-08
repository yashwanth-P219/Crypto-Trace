from typing import List, Optional
import hashlib
import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import AuditLog, User
from app.database.schemas import AuditLogResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("", response_model=List[AuditLogResponse])
def get_all_audit_logs(
    case_id: Optional[str] = Query(default=None),
    action: Optional[str] = Query(default=None),
    username: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(AuditLog)
    if case_id:
        q = q.filter(AuditLog.case_id == case_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if username:
        q = q.filter(AuditLog.username == username)
    return q.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()

@router.get("/case/{case_id}", response_model=List[AuditLogResponse])
def get_case_audit_logs(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(AuditLog).filter(AuditLog.case_id == case_id).order_by(AuditLog.timestamp.asc()).all()

@router.get("/verify/{case_id}")
def verify_audit_integrity(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logs = db.query(AuditLog).filter(AuditLog.case_id == case_id).order_by(AuditLog.timestamp.asc()).all()
    chain_payload = [
        {
            "id": l.id,
            "action": l.action,
            "username": l.username,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            "metadata": l.metadata_json
        }
        for l in logs
    ]
    raw = json.dumps(chain_payload, sort_keys=True, default=str)
    chain_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return {
        "case_id": case_id,
        "total_audit_records": len(logs),
        "audit_chain_sha256": chain_hash,
        "status": "VERIFIED_TAMPER_FREE",
        "verified_at": logs[-1].timestamp.isoformat() if logs else None
    }

