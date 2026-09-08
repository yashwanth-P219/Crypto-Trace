from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from web3 import Web3

from app.database.database import get_db
from app.database.models import User, UserRole
from app.api.auth import get_current_user, require_roles
from app.priority.service import PriorityService
from app.priority.schemas import (
    PriorityItemResponse, PriorityQueueResponse,
    LeadReviewRequest, LeadAssignRequest, LeadNoteRequest,
    PriorityCalculationRequest
)

router = APIRouter(prefix="/priority", tags=["Investigation Priority Engine"])

@router.post("/calculate", response_model=PriorityItemResponse)
def calculate_wallet_priority(
    req: PriorityCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculates deterministic priority ranking for a target wallet address and returns the lead.
    """
    if not Web3.is_address(req.wallet_address):
        raise HTTPException(status_code=400, detail=f"Invalid wallet address: {req.wallet_address}")

    try:
        leads = PriorityService.prioritize_wallet(
            db=db,
            wallet_address=req.wallet_address,
            case_id=req.case_id,
            persist=True
        )
        if not leads:
            raise HTTPException(status_code=400, detail="Could not calculate priority for target wallet")
        return PriorityItemResponse.from_orm(leads[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Priority calculation failed: {str(e)}")

@router.get("/case/{case_id}", response_model=List[PriorityItemResponse])
def get_case_priority_leads(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ranks investigation leads (wallets, transit nodes, liquidations) for a case
    using multi-criteria explainable priority scoring.
    """
    try:
        leads = PriorityService.prioritize_case(db=db, case_id=case_id)
        return [PriorityItemResponse.from_orm(l) for l in leads]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Priority calculation failed: {str(e)}")

@router.get("/wallet/{address}", response_model=List[PriorityItemResponse])
def get_wallet_priority_leads(
    address: str,
    case_id: Optional[str] = None,
    max_hops: int = Query(default=3, ge=1, le=5),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Evaluates priority ranking for a target wallet and its connected flow cluster.
    """
    if not Web3.is_address(address):
        raise HTTPException(status_code=400, detail=f"Invalid wallet address: {address}")

    try:
        leads = PriorityService.prioritize_wallet(
            db=db,
            wallet_address=address,
            case_id=case_id,
            max_hops=max_hops,
            persist=True
        )
        return [PriorityItemResponse.from_orm(l) for l in leads]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Priority calculation failed: {str(e)}")

@router.get("/queue", response_model=PriorityQueueResponse)
def get_priority_queue(
    case_id: Optional[str] = None,
    category: Optional[str] = Query(default=None, description="CRITICAL, HIGH, MEDIUM, LOW"),
    status: Optional[str] = Query(default=None, description="NEW, REVIEWED, IMPORTANT, DISMISSED"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the global investigation priority queue sorted by urgency (CRITICAL down to LOW).
    """
    return PriorityService.get_priority_queue(
        db=db,
        case_id=case_id,
        category=category,
        status=status,
        limit=limit
    )

@router.get("/{priority_id}", response_model=PriorityItemResponse)
def get_priority_lead_by_id(
    priority_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        lead = PriorityService.get_priority_item(db=db, priority_id=priority_id)
        return PriorityItemResponse.from_orm(lead)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{priority_id}/review", response_model=PriorityItemResponse)
def review_priority_lead(
    priority_id: int,
    req: LeadReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INVESTIGATOR, UserRole.SUPERVISOR]))
):
    """
    Allows an authorized investigator or supervisor to mark a lead as REVIEWED, IMPORTANT, or DISMISSED.
    """
    try:
        lead = PriorityService.review_lead(
            db=db,
            priority_id=priority_id,
            status=req.status,
            notes=req.notes,
            username=current_user.username
        )
        return PriorityItemResponse.from_orm(lead)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{priority_id}/assign", response_model=PriorityItemResponse)
def assign_priority_lead(
    priority_id: int,
    req: LeadAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERVISOR, UserRole.ADMINISTRATOR]))
):
    """
    Assigns an urgent lead to an investigator.
    """
    try:
        lead = PriorityService.assign_lead(
            db=db,
            priority_id=priority_id,
            assigned_to=req.assigned_to
        )
        return PriorityItemResponse.from_orm(lead)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{priority_id}/note", response_model=PriorityItemResponse)
def add_lead_note(
    priority_id: int,
    req: LeadNoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INVESTIGATOR, UserRole.SUPERVISOR]))
):
    """
    Appends an investigator note to the priority lead record.
    """
    try:
        lead = PriorityService.add_lead_note(
            db=db,
            priority_id=priority_id,
            note_text=req.note,
            username=current_user.username
        )
        return PriorityItemResponse.from_orm(lead)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
