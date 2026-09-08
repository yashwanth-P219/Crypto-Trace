from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.database import get_db
from app.database.models import User, Case, AuditLog
from app.database.schemas import CopilotQueryRequest, CopilotQueryResponse
from app.api.auth import get_current_user
from app.copilot.investigator_copilot import InvestigationCopilot

router = APIRouter(prefix="/copilot", tags=["Investigation Copilot"])

class CopilotChatRequest(BaseModel):
    message: str
    case_id: Optional[str] = None
    wallet_address: Optional[str] = None

class CopilotCaseAskRequest(BaseModel):
    question: str

@router.post("/query", response_model=CopilotQueryResponse)
def query_copilot(
    req: CopilotQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    copilot = InvestigationCopilot(db)
    result = copilot.query(case_id=req.case_id, question=req.question, user_id=current_user.id)

    # Tamper-aware audit log
    try:
        log = AuditLog(
            user_id=current_user.id,
            username=current_user.username,
            action="COPILOT_QUERY",
            case_id=req.case_id,
            metadata_json={"question": req.question, "category": result.get("category")}
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()

    return result

@router.post("/chat")
def copilot_chat(
    req: CopilotChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    copilot = InvestigationCopilot(db)
    effective_q = req.message
    if req.wallet_address and req.wallet_address not in effective_q:
        effective_q = f"{effective_q} for wallet {req.wallet_address}"
    return copilot.query(case_id=req.case_id, question=effective_q, user_id=current_user.id)

@router.post("/case/{case_id}/ask")
def copilot_case_ask(
    case_id: str,
    req: CopilotCaseAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    copilot = InvestigationCopilot(db)
    return copilot.query(case_id=case_id, question=req.question, user_id=current_user.id)

@router.get("/case/{case_id}/suggestions", response_model=List[str])
def get_copilot_suggestions(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return InvestigationCopilot.get_suggestions(case)
