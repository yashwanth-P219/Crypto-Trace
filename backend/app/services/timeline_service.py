import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database.models import InvestigationTimeline

class TimelineService:
    @staticmethod
    def record_event(
        db: Session,
        case_id: str,
        event_type: str,
        title: str,
        description: str,
        actor: str = "SYSTEM",
        metadata: Optional[Dict[str, Any]] = None
    ) -> InvestigationTimeline:
        event = InvestigationTimeline(
            case_id=case_id,
            event_type=event_type,
            title=title,
            description=description,
            actor=actor,
            timestamp=datetime.datetime.utcnow(),
            metadata_json=metadata or {}
        )
        db.add(event)
        try:
            db.commit()
            db.refresh(event)
        except Exception:
            db.rollback()
        return event

    @staticmethod
    def get_timeline(db: Session, case_id: str):
        return db.query(InvestigationTimeline).filter(
            InvestigationTimeline.case_id == case_id
        ).order_by(InvestigationTimeline.timestamp.asc()).all()
