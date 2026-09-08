import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.database.models import (
    User, UserRole, InvestigatorProfile, InvestigatorApprovalStatus,
    InvestigatorAvailabilityStatus, Case, CaseStatus, AuditLog
)
from app.database.schemas import (
    AvailableInvestigator, InvestigatorProfileResponse,
    InvestigatorApprovalAction, InvestigatorAvailabilityUpdate
)
from app.api.auth import get_current_user, require_roles

router = APIRouter(prefix="/investigators", tags=["Investigator Management"])

@router.get("/available", response_model=List[AvailableInvestigator])
def get_available_investigators(db: Session = Depends(get_db)):
    """
    Returns list of approved and available investigators for victims to select.
    Only approved, active, and available investigators appear.
    """
    results = (
        db.query(User, InvestigatorProfile)
        .join(InvestigatorProfile, User.id == InvestigatorProfile.user_id)
        .filter(
            User.role == UserRole.INVESTIGATOR,
            User.is_active == True,
            InvestigatorProfile.approval_status == InvestigatorApprovalStatus.APPROVED,
            InvestigatorProfile.availability_status == InvestigatorAvailabilityStatus.AVAILABLE
        )
        .all()
    )

    available_list = []
    for user, prof in results:
        # Count active assigned cases
        active_cases = (
            db.query(func.count(Case.case_id))
            .filter(
                Case.assigned_investigator_id == user.id,
                ~Case.status.in_([CaseStatus.CLOSED, CaseStatus.RESOLVED, CaseStatus.REJECTED])
            )
            .scalar() or 0
        )
        available_list.append(AvailableInvestigator(
            id=user.id,
            full_name=user.full_name,
            username=user.username,
            organization=prof.organization,
            department=prof.department,
            experience_years=prof.experience_years,
            specialization=prof.specialization,
            availability_status=prof.availability_status.value,
            active_cases_count=active_cases
        ))

    return available_list

@router.get("/profile/me", response_model=InvestigatorProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns current investigator's profile, approval state, and case load."""
    if current_user.role != UserRole.INVESTIGATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Profile is only available for investigators"
        )

    prof = db.query(InvestigatorProfile).filter(InvestigatorProfile.user_id == current_user.id).first()
    if not prof:
        # Create empty profile if missing
        prof = InvestigatorProfile(
            user_id=current_user.id,
            approval_status=InvestigatorApprovalStatus.PENDING,
            availability_status=InvestigatorAvailabilityStatus.OFFLINE
        )
        db.add(prof)
        db.commit()
        db.refresh(prof)

    active_cases = (
        db.query(func.count(Case.case_id))
        .filter(
            Case.assigned_investigator_id == current_user.id,
            ~Case.status.in_([CaseStatus.CLOSED, CaseStatus.RESOLVED, CaseStatus.REJECTED])
        )
        .scalar() or 0
    )

    return InvestigatorProfileResponse(
        id=prof.id,
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        phone_number=current_user.phone_number,
        organization=prof.organization,
        department=prof.department,
        experience_years=prof.experience_years,
        specialization=prof.specialization,
        badge_id=prof.badge_id,
        approval_status=prof.approval_status.value,
        availability_status=prof.availability_status.value,
        rejection_reason=prof.rejection_reason,
        active_cases_count=active_cases,
        created_at=prof.created_at
    )

@router.patch("/availability", response_model=InvestigatorProfileResponse)
def update_availability(
    payload: InvestigatorAvailabilityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Investigator updates their availability status (AVAILABLE, BUSY, OFFLINE)."""
    if current_user.role != UserRole.INVESTIGATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only investigators can update availability"
        )

    prof = db.query(InvestigatorProfile).filter(InvestigatorProfile.user_id == current_user.id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Investigator profile not found")

    if prof.approval_status != InvestigatorApprovalStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot change availability while approval status is {prof.approval_status.value}. Must be APPROVED."
        )

    try:
        new_status = InvestigatorAvailabilityStatus(payload.availability_status.upper())
        prof.availability_status = new_status
        db.commit()
        db.refresh(prof)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid availability status. Options: {[s.value for s in InvestigatorAvailabilityStatus]}"
        )

    return get_my_profile(current_user=current_user, db=db)

@router.get("/admin/list", response_model=List[InvestigatorProfileResponse])
def list_investigators_for_admin(
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.SUPERVISOR])),
    db: Session = Depends(get_db)
):
    """Admin/Supervisor lists all investigators with approval and availability details."""
    query = (
        db.query(User, InvestigatorProfile)
        .join(InvestigatorProfile, User.id == InvestigatorProfile.user_id)
        .filter(User.role == UserRole.INVESTIGATOR)
    )

    if status_filter:
        try:
            status_enum = InvestigatorApprovalStatus(status_filter.upper())
            query = query.filter(InvestigatorProfile.approval_status == status_enum)
        except ValueError:
            pass

    items = query.order_by(InvestigatorProfile.created_at.desc()).all()
    response_list = []
    for user, prof in items:
        active_cases = (
            db.query(func.count(Case.case_id))
            .filter(
                Case.assigned_investigator_id == user.id,
                ~Case.status.in_([CaseStatus.CLOSED, CaseStatus.RESOLVED, CaseStatus.REJECTED])
            )
            .scalar() or 0
        )
        response_list.append(InvestigatorProfileResponse(
            id=prof.id,
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone_number=user.phone_number,
            organization=prof.organization,
            department=prof.department,
            experience_years=prof.experience_years,
            specialization=prof.specialization,
            badge_id=prof.badge_id,
            approval_status=prof.approval_status.value,
            availability_status=prof.availability_status.value,
            rejection_reason=prof.rejection_reason,
            active_cases_count=active_cases,
            created_at=prof.created_at
        ))

    return response_list

@router.post("/admin/{user_id}/approve", response_model=InvestigatorProfileResponse)
def approve_investigator(
    user_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR])),
    db: Session = Depends(get_db)
):
    """Admin approves pending investigator application."""
    prof = db.query(InvestigatorProfile).filter(InvestigatorProfile.user_id == user_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Investigator profile not found")

    prof.approval_status = InvestigatorApprovalStatus.APPROVED
    prof.availability_status = InvestigatorAvailabilityStatus.AVAILABLE
    prof.approved_by_id = current_user.id
    prof.approved_at = datetime.datetime.utcnow()
    prof.rejection_reason = None
    db.commit()

    # Log action
    log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="INVESTIGATOR_APPROVED",
        metadata_json={"approved_user_id": user_id}
    )
    db.add(log)
    db.commit()

    user = db.query(User).filter(User.id == user_id).first()
    return InvestigatorProfileResponse(
        id=prof.id,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        organization=prof.organization,
        department=prof.department,
        experience_years=prof.experience_years,
        specialization=prof.specialization,
        badge_id=prof.badge_id,
        approval_status=prof.approval_status.value,
        availability_status=prof.availability_status.value,
        rejection_reason=prof.rejection_reason,
        active_cases_count=0,
        created_at=prof.created_at
    )

@router.post("/admin/{user_id}/reject", response_model=InvestigatorProfileResponse)
def reject_investigator(
    user_id: int,
    payload: InvestigatorApprovalAction,
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR])),
    db: Session = Depends(get_db)
):
    """Admin rejects investigator application with formal justification."""
    prof = db.query(InvestigatorProfile).filter(InvestigatorProfile.user_id == user_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Investigator profile not found")

    prof.approval_status = InvestigatorApprovalStatus.REJECTED
    prof.availability_status = InvestigatorAvailabilityStatus.OFFLINE
    prof.rejection_reason = payload.rejection_reason or "Application rejected by administrator."
    prof.approved_by_id = current_user.id
    prof.approved_at = datetime.datetime.utcnow()
    db.commit()

    log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="INVESTIGATOR_REJECTED",
        metadata_json={"rejected_user_id": user_id, "reason": prof.rejection_reason}
    )
    db.add(log)
    db.commit()

    user = db.query(User).filter(User.id == user_id).first()
    return InvestigatorProfileResponse(
        id=prof.id,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        organization=prof.organization,
        department=prof.department,
        experience_years=prof.experience_years,
        specialization=prof.specialization,
        badge_id=prof.badge_id,
        approval_status=prof.approval_status.value,
        availability_status=prof.availability_status.value,
        rejection_reason=prof.rejection_reason,
        active_cases_count=0,
        created_at=prof.created_at
    )

@router.post("/admin/{user_id}/suspend", response_model=InvestigatorProfileResponse)
def suspend_investigator(
    user_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR])),
    db: Session = Depends(get_db)
):
    """Admin suspends investigator access."""
    prof = db.query(InvestigatorProfile).filter(InvestigatorProfile.user_id == user_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Investigator profile not found")

    prof.approval_status = InvestigatorApprovalStatus.SUSPENDED
    prof.availability_status = InvestigatorAvailabilityStatus.OFFLINE
    db.commit()

    log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="INVESTIGATOR_SUSPENDED",
        metadata_json={"suspended_user_id": user_id}
    )
    db.add(log)
    db.commit()

    user = db.query(User).filter(User.id == user_id).first()
    return InvestigatorProfileResponse(
        id=prof.id,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        organization=prof.organization,
        department=prof.department,
        experience_years=prof.experience_years,
        specialization=prof.specialization,
        badge_id=prof.badge_id,
        approval_status=prof.approval_status.value,
        availability_status=prof.availability_status.value,
        rejection_reason=prof.rejection_reason,
        active_cases_count=0,
        created_at=prof.created_at
    )

@router.post("/admin/{user_id}/reactivate", response_model=InvestigatorProfileResponse)
def reactivate_investigator(
    user_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR])),
    db: Session = Depends(get_db)
):
    """Admin reactivates suspended or rejected investigator."""
    prof = db.query(InvestigatorProfile).filter(InvestigatorProfile.user_id == user_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Investigator profile not found")

    prof.approval_status = InvestigatorApprovalStatus.APPROVED
    prof.rejection_reason = None
    db.commit()

    log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="INVESTIGATOR_REACTIVATED",
        metadata_json={"reactivated_user_id": user_id}
    )
    db.add(log)
    db.commit()

    user = db.query(User).filter(User.id == user_id).first()
    return InvestigatorProfileResponse(
        id=prof.id,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        organization=prof.organization,
        department=prof.department,
        experience_years=prof.experience_years,
        specialization=prof.specialization,
        badge_id=prof.badge_id,
        approval_status=prof.approval_status.value,
        availability_status=prof.availability_status.value,
        rejection_reason=prof.rejection_reason,
        active_cases_count=0,
        created_at=prof.created_at
    )
