import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User, UserRole, Report, ReportStatus, Case, AuditLog
from app.database.schemas import ReportCreate, ReportReview, ReportResponse
from app.api.auth import get_current_user, require_roles
from app.reports.report_generator import ReportGenerator

router = APIRouter(prefix="/reports", tags=["Forensic Reports"])

@router.post("/generate", response_model=ReportResponse)
def generate_investigation_report(
    req: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INVESTIGATOR, UserRole.SUPERVISOR]))
):
    try:
        return ReportGenerator.generate_case_report(
            db=db,
            case_id=req.case_id,
            investigator_user=current_user,
            custom_title=req.title
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/case/{case_id}", response_model=List[ReportResponse])
def get_reports_for_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Report).filter(Report.case_id == case_id).order_by(Report.generated_at.desc()).all()

@router.get("/{report_id}", response_model=ReportResponse)
def get_report_by_id(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.patch("/{report_id}/review", response_model=ReportResponse)
def review_report(
    report_id: str,
    review_in: ReportReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPERVISOR, UserRole.ADMINISTRATOR]))
):
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = review_in.status
    report.supervisor_id = current_user.id
    report.supervisor_comments = review_in.supervisor_comments
    if review_in.status == ReportStatus.APPROVED:
        report.approved_at = datetime.datetime.utcnow()
        # Update case status to CLOSED or REPORT_PENDING
        case = db.query(Case).filter(Case.case_id == report.case_id).first()
        if case:
            case.status = "CLOSED"

    # Audit log
    log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=f"REPORT_{review_in.status.value}",
        case_id=report.case_id,
        metadata_json={
            "report_id": report_id,
            "supervisor": current_user.full_name,
            "comments": review_in.supervisor_comments
        }
    )
    db.add(log)
    db.commit()
    db.refresh(report)
    return report

@router.get("/{report_id}/pdf")
def download_report_pdf(
    report_id: str,
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    pdf_bytes = ReportGenerator.build_pdf_bytes(report)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{report_id}.pdf"',
            "Content-Type": "application/pdf"
        }
    )

@router.get("/{report_id}/json")
def download_report_json(
    report_id: str,
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    json_str = ReportGenerator.build_json_str(report)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{report_id}.json"',
            "Content-Type": "application/json"
        }
    )

@router.get("/{report_id}/csv")
def download_report_csv(
    report_id: str,
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    csv_str = ReportGenerator.build_csv_str(report)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{report_id}.csv"',
            "Content-Type": "text/csv"
        }
    )

