from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User, UserRole, Evidence
from app.database.schemas import EvidenceCreate, EvidenceResponse
from app.api.auth import get_current_user, require_roles
from app.evidence.evidence_service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["Evidence Locker"])

@router.post("", response_model=EvidenceResponse)
def save_evidence_item(
    evidence_in: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INVESTIGATOR, UserRole.SUPERVISOR]))
):
    return EvidenceService.save_evidence(db, evidence_in, current_user.username)

@router.get("/{case_id}", response_model=List[EvidenceResponse])
def get_case_evidence(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return EvidenceService.get_case_evidence(db, case_id)
