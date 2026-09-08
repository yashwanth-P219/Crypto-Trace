import hashlib
import uuid
import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.models import Evidence, AuditLog
from app.database.schemas import EvidenceCreate

class EvidenceService:
    @staticmethod
    def compute_integrity_hash(
        case_id: str,
        tx_hash: str,
        from_address: str,
        to_address: str,
        amount: float,
        timestamp_str: str
    ) -> str:
        payload = f"{case_id}:{tx_hash}:{from_address.lower()}:{to_address.lower()}:{amount}:{timestamp_str}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def save_evidence(
        db: Session,
        evidence_in: EvidenceCreate,
        username: str
    ) -> Evidence:
        evidence_id = f"EV-{uuid.uuid4().hex[:10].upper()}"
        ts = evidence_in.timestamp or datetime.datetime.utcnow()
        integrity_hash = EvidenceService.compute_integrity_hash(
            case_id=evidence_in.case_id,
            tx_hash=evidence_in.transaction_hash,
            from_address=evidence_in.from_address,
            to_address=evidence_in.to_address,
            amount=evidence_in.amount,
            timestamp_str=ts.isoformat()
        )

        evidence = Evidence(
            evidence_id=evidence_id,
            case_id=evidence_in.case_id,
            blockchain=evidence_in.blockchain,
            wallet=evidence_in.wallet,
            transaction_hash=evidence_in.transaction_hash,
            block_number=evidence_in.block_number,
            timestamp=ts,
            from_address=evidence_in.from_address,
            to_address=evidence_in.to_address,
            amount=evidence_in.amount,
            finding_type=evidence_in.finding_type,
            tag=evidence_in.tag,
            source=evidence_in.source,
            investigator_notes=evidence_in.investigator_notes,
            importance=evidence_in.importance,
            integrity_hash=integrity_hash
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)

        # Audit log
        log = AuditLog(
            username=username,
            action="EVIDENCE_SAVED",
            case_id=evidence_in.case_id,
            metadata_json={
                "evidence_id": evidence_id,
                "tx_hash": evidence_in.transaction_hash,
                "tag": evidence_in.tag,
                "integrity_hash": integrity_hash
            }
        )
        db.add(log)
        db.commit()

        return evidence

    @staticmethod
    def get_case_evidence(db: Session, case_id: str) -> List[Evidence]:
        return db.query(Evidence).filter(Evidence.case_id == case_id).all()
