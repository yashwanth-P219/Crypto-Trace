import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import AddressLabel, User, UserRole, AuditLog
from app.database.schemas import AddressLabelCreate, AddressLabelResponse
from app.api.auth import get_current_user, require_roles

router = APIRouter(prefix="/labels", tags=["Address Labels & VASP Intel"])

@router.get("", response_model=List[AddressLabelResponse])
def get_address_labels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(AddressLabel).order_by(AddressLabel.entity_name.asc()).all()

@router.post("", response_model=AddressLabelResponse)
def create_or_update_label(
    label_in: AddressLabelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMINISTRATOR, UserRole.INVESTIGATOR]))
):
    norm_addr = label_in.address.lower()
    lbl = db.query(AddressLabel).filter(
        AddressLabel.address.ilike(norm_addr),
        AddressLabel.blockchain == label_in.blockchain
    ).first()

    if lbl:
        lbl.entity_name = label_in.entity_name
        lbl.entity_type = label_in.entity_type
        lbl.source = label_in.source
        lbl.confidence = label_in.confidence
        lbl.notes = label_in.notes
        lbl.last_verified = datetime.datetime.utcnow()
    else:
        lbl = AddressLabel(
            address=label_in.address,
            blockchain=label_in.blockchain,
            entity_name=label_in.entity_name,
            entity_type=label_in.entity_type,
            source=label_in.source,
            confidence=label_in.confidence,
            notes=label_in.notes,
            last_verified=datetime.datetime.utcnow()
        )
        db.add(lbl)

    # Audit log
    log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="LABEL_CHANGED",
        metadata_json={
            "address": label_in.address,
            "entity_name": label_in.entity_name,
            "type": label_in.entity_type.value
        }
    )
    db.add(log)
    db.commit()
    db.refresh(lbl)
    return lbl
