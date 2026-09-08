import uuid
import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.database.models import (
    Case, User, UserRole, CaseStatus, CasePriority, AuditLog,
    CaseAssignment, CaseAssignmentStatus, Notification,
    InvestigatorProfile, InvestigatorApprovalStatus
)
from app.database.schemas import CaseCreate, CaseUpdate
from app.services.timeline_service import TimelineService

class CaseService:
    @staticmethod
    def create_case(db: Session, case_in: CaseCreate, user: User) -> Case:
        # Dynamic case ID & sequential case number (CASE-YYYY-XXXXX)
        year = datetime.datetime.utcnow().year
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        total_cases = db.query(func.count(Case.case_id)).scalar() or 0
        case_number = f"CASE-{year}-{total_cases + 1:05d}"

        ref = case_in.complaint_reference or f"CR-{year}-CYBER-{uuid.uuid4().hex[:6].upper()}"
        victim_name_val = case_in.victim_name or user.full_name or user.username
        title = case_in.title or f"Complaint: {victim_name_val} ({case_in.amount_lost} {case_in.currency})"

        incident_dt = case_in.incident_date or datetime.datetime.utcnow()
        victim_id = user.id if user.role == UserRole.VICTIM else None

        # Determine assignment & initial status
        assigned_id = None
        initial_status = CaseStatus.NEW
        chosen_inv_id = case_in.preferred_investigator_id or case_in.investigator_id

        if user.role == UserRole.INVESTIGATOR:
            assigned_id = user.id
            initial_status = CaseStatus.ACCEPTED
        elif chosen_inv_id:
            # Verify investigator is approved
            inv = db.query(User).filter(
                User.id == chosen_inv_id,
                User.role == UserRole.INVESTIGATOR,
                User.is_active == True
            ).first()
            if inv:
                prof = db.query(InvestigatorProfile).filter(InvestigatorProfile.user_id == inv.id).first()
                if prof and prof.approval_status == InvestigatorApprovalStatus.APPROVED:
                    assigned_id = inv.id
                    initial_status = CaseStatus.ASSIGNED

        case = Case(
            case_id=case_id,
            case_number=case_number,
            title=title,
            victim_id=victim_id,
            victim_name=victim_name_val,
            complaint_reference=ref,
            amount_lost=case_in.amount_lost,
            currency=case_in.currency,
            incident_date=incident_dt,
            description=case_in.description,
            suspect_wallet=case_in.suspect_wallet,
            blockchain=case_in.blockchain,
            transaction_hash=case_in.transaction_hash,
            status=initial_status,
            priority=case_in.priority,
            assigned_investigator_id=assigned_id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        # Create Assignment record and dispatch notification if assigned
        if assigned_id:
            assignment = CaseAssignment(
                case_id=case_id,
                victim_id=victim_id,
                investigator_id=assigned_id,
                status=CaseAssignmentStatus.ACCEPTED if user.role == UserRole.INVESTIGATOR else CaseAssignmentStatus.PENDING,
                assigned_by_id=user.id,
                assigned_at=datetime.datetime.utcnow(),
                notes=f"Assigned at creation by {user.full_name} ({user.role.value})"
            )
            db.add(assignment)

            if user.role == UserRole.VICTIM:
                # Notify investigator
                notif = Notification(
                    user_id=assigned_id,
                    case_id=case_id,
                    notification_type="CASE_ASSIGNED",
                    title="New Investigation Assigned",
                    message=f"Case {case_number} has been assigned to you by complainant {case_in.victim_name}."
                )
                db.add(notif)

            db.commit()

        # Record timeline event
        TimelineService.record_event(
            db=db,
            case_id=case_id,
            event_type="CASE_CREATED",
            title=f"Case Registered: {case_number}",
            description=f"Complaint filed for loss of {case_in.amount_lost} {case_in.currency}. Suspect wallet: {case_in.suspect_wallet or 'Pending discovery'}.",
            actor=user.username,
            metadata={"case_number": case_number, "priority": case_in.priority.value}
        )

        # Audit Log
        log = AuditLog(
            user_id=user.id,
            username=user.username,
            action="CASE_CREATED",
            case_id=case_id,
            metadata_json={
                "case_number": case_number,
                "complaint_reference": ref,
                "suspect_wallet": case_in.suspect_wallet,
                "assigned_investigator_id": assigned_id
            }
        )
        db.add(log)
        db.commit()
        return case

    @staticmethod
    def get_cases(db: Session, user: User) -> List[Case]:
        if user.role == UserRole.VICTIM:
            return db.query(Case).filter(
                or_(Case.victim_id == user.id, Case.victim_name == user.full_name)
            ).order_by(Case.created_at.desc()).all()

        if user.role == UserRole.INVESTIGATOR:
            return db.query(Case).filter(
                or_(
                    Case.assigned_investigator_id == user.id,
                    Case.status.in_([CaseStatus.NEW, CaseStatus.ASSIGNED])
                )
            ).order_by(Case.created_at.desc()).all()

        # SUPERVISOR and ADMINISTRATOR see all cases
        return db.query(Case).order_by(Case.created_at.desc()).all()

    @staticmethod
    def get_case_by_id(db: Session, case_id: str, user: Optional[User] = None) -> Optional[Case]:
        case = db.query(Case).filter(
            or_(Case.case_id == case_id, Case.case_number == case_id)
        ).first()
        if not case:
            return None

        if user and user.role == UserRole.VICTIM:
            if case.victim_id and case.victim_id != user.id and case.victim_name != user.full_name:
                return None

        return case

    @staticmethod
    def accept_case(db: Session, case_id: str, user: User) -> Case:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise ValueError("Case not found")

        case.assigned_investigator_id = user.id
        case.status = CaseStatus.ACCEPTED
        case.updated_at = datetime.datetime.utcnow()

        # Update assignment record
        assignment = db.query(CaseAssignment).filter(
            CaseAssignment.case_id == case_id,
            CaseAssignment.investigator_id == user.id
        ).first()

        if assignment:
            assignment.status = CaseAssignmentStatus.ACCEPTED
            assignment.accepted_at = datetime.datetime.utcnow()
        else:
            assignment = CaseAssignment(
                case_id=case_id,
                victim_id=case.victim_id,
                investigator_id=user.id,
                status=CaseAssignmentStatus.ACCEPTED,
                assigned_by_id=user.id,
                accepted_at=datetime.datetime.utcnow(),
                notes="Accepted directly by investigator"
            )
            db.add(assignment)

        # Notify victim if registered
        if case.victim_id:
            notif = Notification(
                user_id=case.victim_id,
                case_id=case_id,
                notification_type="CASE_ACCEPTED",
                title="Investigator Accepted Your Case",
                message=f"Investigator {user.full_name} has accepted your complaint {case.case_number or case_id} and initiated preliminary review."
            )
            db.add(notif)

        TimelineService.record_event(
            db=db,
            case_id=case_id,
            event_type="STATUS_CHANGED",
            title="Case Accepted by Investigator",
            description=f"Investigator {user.full_name} accepted the investigation assignment.",
            actor=user.username
        )

        db.commit()
        db.refresh(case)
        return case

    @staticmethod
    def start_investigation(db: Session, case_id: str, user: User) -> Case:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise ValueError("Case not found")

        case.status = CaseStatus.UNDER_INVESTIGATION
        case.updated_at = datetime.datetime.utcnow()

        TimelineService.record_event(
            db=db,
            case_id=case_id,
            event_type="STATUS_CHANGED",
            title="Active Investigation Commenced",
            description="Investigator commenced blockchain transaction indexing, graph traversal, and pattern analysis.",
            actor=user.username
        )

        if case.victim_id:
            notif = Notification(
                user_id=case.victim_id,
                case_id=case_id,
                notification_type="STATUS_UPDATE",
                title="Investigation Active",
                message=f"Forensic blockchain analysis is now actively underway for Case {case.case_number or case_id}."
            )
            db.add(notif)

        db.commit()
        db.refresh(case)
        return case

    @staticmethod
    def update_case(db: Session, case_id: str, updates: CaseUpdate, user: User) -> Optional[Case]:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            return None

        update_data = updates.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(case, key, val)

        case.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(case)

        log = AuditLog(
            user_id=user.id,
            username=user.username,
            action="CASE_UPDATED",
            case_id=case_id,
            metadata_json=update_data
        )
        db.add(log)
        db.commit()
        return case

