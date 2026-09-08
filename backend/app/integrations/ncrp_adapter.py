import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.database.models import Case, Evidence, Transaction, User

class NCRPAdapter:
    """
    Adapter for interoperability with National Cyber Crime Reporting Portal (NCRP)
    and I4C SAHYOG Portal for cryptocurrency fraud reporting.
    """

    @staticmethod
    def export_ncrp_format(case: Case, db: Session) -> Dict[str, Any]:
        """
        Formats case data according to NCRP Standard Cyber Fraud Ingestion Schema.
        """
        evidence_items = db.query(Evidence).filter(Evidence.case_id == case.case_id).all()
        transactions = db.query(Transaction).filter(
            (Transaction.case_id == case.case_id) |
            (Transaction.from_address.ilike(case.suspect_wallet or "")) |
            (Transaction.to_address.ilike(case.suspect_wallet or ""))
        ).all()

        victim_phone = None
        victim_email = None
        if case.victim:
            victim_phone = case.victim.phone_number
            victim_email = case.victim.email

        investigator_info = None
        if case.assigned_investigator:
            prof = case.assigned_investigator.investigator_profile
            investigator_info = {
                "officer_name": case.assigned_investigator.full_name,
                "badge_number": prof.badge_id if prof and prof.badge_id else "CYBER-INV",
                "department": prof.department if prof and prof.department else "Cyber Crime Cell",
                "email": case.assigned_investigator.email,
                "phone": case.assigned_investigator.phone_number
            }

        return {
            "schema_version": "NCRP-CYBERFRAUD-2.1",
            "portal": "National Cyber Crime Reporting Portal (cybercrime.gov.in)",
            "acknowledgement_number": case.case_number or f"NCRP-{case.case_id[:8].upper()}",
            "complaint_reference": case.complaint_reference or case.case_number,
            "incident_category": "Cryptocurrency Fraud / Investment Scam",
            "sub_category": "Fraudulent Crypto Transfer / Exchange Layering",
            "filing_timestamp": case.created_at.isoformat() if case.created_at else datetime.datetime.utcnow().isoformat(),
            "incident_date": case.incident_date.isoformat() if case.incident_date else None,
            "financial_loss": {
                "reported_amount": case.amount_lost or 0.0,
                "currency": case.currency or "INR",
                "amount_in_inr": case.amount_lost if case.currency == "INR" else None
            },
            "complainant": {
                "name": case.victim_name or "Confidential",
                "email": victim_email,
                "phone_number": victim_phone,
                "user_id": case.victim_id
            },
            "suspect_identifiers": {
                "suspect_wallet_address": case.suspect_wallet,
                "initial_transaction_hash": case.transaction_hash,
                "blockchain_network": case.blockchain or "Ethereum Sepolia",
                "identified_nexus_exchanges": [
                    tx.to_address for tx in transactions if tx.to_address
                ][:5]
            },
            "investigation": {
                "case_status": case.status.value if hasattr(case.status, "value") else str(case.status),
                "case_priority": case.priority.value if hasattr(case.priority, "value") else str(case.priority),
                "investigating_agency": investigator_info
            },
            "digital_evidence": [
                {
                    "evidence_id": e.evidence_id,
                    "tag": e.tag,
                    "sha256_hash": e.integrity_hash,
                    "transaction_hash": e.transaction_hash,
                    "collected_at": e.retrieved_at.isoformat() if e.retrieved_at else None
                }
                for e in evidence_items
            ],
            "transaction_count": len(transactions),
            "export_timestamp": datetime.datetime.utcnow().isoformat()
        }

    @staticmethod
    def export_sahyog_format(case: Case, db: Session) -> Dict[str, Any]:
        """
        Formats case data according to I4C SAHYOG (Inter-Agency Coordination) Schema.
        """
        transactions = db.query(Transaction).filter(
            (Transaction.case_id == case.case_id) |
            (Transaction.from_address.ilike(case.suspect_wallet or "")) |
            (Transaction.to_address.ilike(case.suspect_wallet or ""))
        ).all()

        return {
            "sahyog_version": "SAHYOG-I4C-V1",
            "request_type": "INTER_AGENCY_CRYPTO_INTELLIGENCE",
            "case_identifier": case.case_number or f"CASE-{case.case_id[:8].upper()}",
            "suspect_asset": {
                "wallet_address": case.suspect_wallet,
                "blockchain": case.blockchain or "Ethereum",
                "first_reported_tx": case.transaction_hash,
                "total_flow_count": len(transactions)
            },
            "alert_level": "RED" if case.priority.value in ["HIGH", "CRITICAL"] else "AMBER",
            "requesting_officer": {
                "name": case.assigned_investigator.full_name if case.assigned_investigator else "Pending Assignment",
                "badge": (case.assigned_investigator.investigator_profile.badge_id if case.assigned_investigator and case.assigned_investigator.investigator_profile and case.assigned_investigator.investigator_profile.badge_id else "N/A"),
                "unit": (case.assigned_investigator.investigator_profile.department if case.assigned_investigator and case.assigned_investigator.investigator_profile and case.assigned_investigator.investigator_profile.department else "Cyber Crime Division")
            },
            "suggested_action": "Freeze VASP accounts associated with destination clusters and request Section 91 CrPC compliance.",
            "generated_at": datetime.datetime.utcnow().isoformat()
        }
