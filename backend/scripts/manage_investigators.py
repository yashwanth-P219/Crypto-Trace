"""
SIH26183 Database Investigator Management Utility
==================================================
Allows administrators to inspect, approve, reject, or suspend investigator accounts
directly in the database without requiring an in-application frontend admin panel.

Direct SQL Equivalents:
-----------------------
1. List pending investigators:
   SELECT u.id, u.username, u.full_name, u.email, p.badge_id, p.organization, p.approval_status
   FROM users u JOIN investigator_profiles p ON u.id = p.user_id
   WHERE p.approval_status = 'PENDING';

2. Approve an investigator:
   UPDATE investigator_profiles
   SET approval_status = 'APPROVED', availability_status = 'AVAILABLE', approved_at = NOW()
   WHERE user_id = (SELECT id FROM users WHERE username = '<username>');

3. Approve all pending investigators:
   UPDATE investigator_profiles
   SET approval_status = 'APPROVED', availability_status = 'AVAILABLE', approved_at = NOW()
   WHERE approval_status = 'PENDING';

Usage:
------
python scripts/manage_investigators.py --list
python scripts/manage_investigators.py --approve <username_or_badge>
python scripts/manage_investigators.py --approve-all
python scripts/manage_investigators.py --reject <username_or_badge> [--reason "reason"]
python scripts/manage_investigators.py --suspend <username_or_badge>
python scripts/manage_investigators.py --pending <username_or_badge>
"""

import sys
import os
import argparse
from datetime import datetime

# Add backend root to sys.path so app modules import properly
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database.database import SessionLocal
from app.database.models import (
    User,
    UserRole,
    InvestigatorProfile,
    InvestigatorApprovalStatus,
    InvestigatorAvailabilityStatus,
    AuditLog
)


def list_investigators(db):
    profiles = db.query(InvestigatorProfile).join(User, InvestigatorProfile.user_id == User.id).all()
    if not profiles:
        print("\n[!] No investigator profiles found in database.")
        return

    print(f"\n{'='*96}")
    print(f"{'INVESTIGATOR DATABASE REGISTRY':^96}")
    print(f"{'='*96}")
    header = f"{'UID':<5} | {'Username':<18} | {'Officer Name':<20} | {'Badge ID':<12} | {'Status':<11} | {'Availability':<12}"
    print(header)
    print("-" * 96)

    for p in profiles:
        u = p.user
        uid = str(u.id) if u else "N/A"
        uname = (u.username or "N/A")[:18]
        fname = (u.full_name or "N/A")[:20]
        badge = (p.badge_id or "N/A")[:12]
        status = p.approval_status.value if hasattr(p.approval_status, 'value') else str(p.approval_status)
        avail = p.availability_status.value if hasattr(p.availability_status, 'value') else str(p.availability_status)
        
        if status == "APPROVED":
            status_disp = f"[+] {status}"
        elif status == "PENDING":
            status_disp = f"[?] {status}"
        else:
            status_disp = f"[-] {status}"
            
        print(f"{uid:<5} | {uname:<18} | {fname:<20} | {badge:<12} | {status_disp:<11} | {avail:<12}")

    print(f"{'='*96}\n")


def find_investigator(db, identifier):
    """Find investigator profile by username, user ID, or badge ID."""
    # Try user ID
    if identifier.isdigit():
        prof = db.query(InvestigatorProfile).filter(InvestigatorProfile.user_id == int(identifier)).first()
        if prof:
            return prof

    # Try username
    user = db.query(User).filter(User.username.ilike(identifier)).first()
    if user:
        prof = db.query(InvestigatorProfile).filter(InvestigatorProfile.user_id == user.id).first()
        if prof:
            return prof

    # Try badge ID
    prof = db.query(InvestigatorProfile).filter(InvestigatorProfile.badge_id.ilike(identifier)).first()
    return prof


def approve_investigator(db, identifier):
    prof = find_investigator(db, identifier)
    if not prof:
        print(f"\n[ERROR] Investigator '{identifier}' not found in database.")
        return False

    prof.approval_status = InvestigatorApprovalStatus.APPROVED
    prof.availability_status = InvestigatorAvailabilityStatus.AVAILABLE
    prof.approved_at = datetime.utcnow()
    prof.rejection_reason = None

    u = prof.user
    log = AuditLog(
        user_id=u.id if u else None,
        username=u.username if u else "unknown",
        action="DB_ADMIN_APPROVE_INVESTIGATOR",
        metadata_json={
            "approved_by": "DATABASE_ADMIN_CLI",
            "approval_status": "APPROVED",
            "availability_status": "AVAILABLE"
        }
    )
    db.add(log)
    db.commit()

    print(f"\n[SUCCESS] Approved investigator: {u.full_name if u else 'N/A'} (@{u.username if u else identifier})")
    print(f"          Status set to: APPROVED, Availability: AVAILABLE")
    print(f"          Investigator is now immediately eligible to receive victim cases and lead investigations.\n")
    return True


def approve_all_pending(db):
    pending = db.query(InvestigatorProfile).filter(
        InvestigatorProfile.approval_status == InvestigatorApprovalStatus.PENDING
    ).all()

    if not pending:
        print("\n[*] No pending investigators to approve.")
        return

    count = 0
    now = datetime.utcnow()
    for prof in pending:
        prof.approval_status = InvestigatorApprovalStatus.APPROVED
        prof.availability_status = InvestigatorAvailabilityStatus.AVAILABLE
        prof.approved_at = now
        prof.rejection_reason = None
        u = prof.user
        log = AuditLog(
            user_id=u.id if u else None,
            username=u.username if u else "unknown",
            action="DB_ADMIN_APPROVE_ALL_INVESTIGATORS",
            metadata_json={"approved_by": "DATABASE_ADMIN_CLI"}
        )
        db.add(log)
        count += 1

    db.commit()
    print(f"\n[SUCCESS] Approved all {count} pending investigator(s). They are now APPROVED and AVAILABLE.")


def reject_investigator(db, identifier, reason="Administrative decision"):
    prof = find_investigator(db, identifier)
    if not prof:
        print(f"\n[ERROR] Investigator '{identifier}' not found in database.")
        return False

    prof.approval_status = InvestigatorApprovalStatus.REJECTED
    prof.availability_status = InvestigatorAvailabilityStatus.OFFLINE
    prof.rejection_reason = reason

    u = prof.user
    log = AuditLog(
        user_id=u.id if u else None,
        username=u.username if u else "unknown",
        action="DB_ADMIN_REJECT_INVESTIGATOR",
        metadata_json={"rejected_by": "DATABASE_ADMIN_CLI", "reason": reason}
    )
    db.add(log)
    db.commit()

    print(f"\n[SUCCESS] Rejected investigator: {u.full_name if u else 'N/A'} (@{u.username if u else identifier})")
    print(f"          Reason: {reason}\n")
    return True


def suspend_investigator(db, identifier, reason="Administrative suspension"):
    prof = find_investigator(db, identifier)
    if not prof:
        print(f"\n[ERROR] Investigator '{identifier}' not found in database.")
        return False

    prof.approval_status = InvestigatorApprovalStatus.SUSPENDED
    prof.availability_status = InvestigatorAvailabilityStatus.OFFLINE
    prof.rejection_reason = reason

    u = prof.user
    log = AuditLog(
        user_id=u.id if u else None,
        username=u.username if u else "unknown",
        action="DB_ADMIN_SUSPEND_INVESTIGATOR",
        metadata_json={"suspended_by": "DATABASE_ADMIN_CLI", "reason": reason}
    )
    db.add(log)
    db.commit()

    print(f"\n[SUCCESS] Suspended investigator: {u.full_name if u else 'N/A'} (@{u.username if u else identifier})")
    return True


def set_pending_investigator(db, identifier):
    prof = find_investigator(db, identifier)
    if not prof:
        print(f"\n[ERROR] Investigator '{identifier}' not found in database.")
        return False

    prof.approval_status = InvestigatorApprovalStatus.PENDING
    prof.availability_status = InvestigatorAvailabilityStatus.OFFLINE
    prof.approved_at = None
    prof.rejection_reason = None
    db.commit()

    u = prof.user
    print(f"\n[SUCCESS] Reset investigator: {u.full_name if u else 'N/A'} (@{u.username if u else identifier}) to PENDING status.")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="SIH26183 Database Investigator Management Utility (Admin Database Tool)"
    )
    parser.add_argument("--list", action="store_true", help="List all investigators in database")
    parser.add_argument("--approve", metavar="IDENTIFIER", help="Approve investigator by username, user ID, or badge ID")
    parser.add_argument("--approve-all", action="store_true", help="Approve all currently pending investigators")
    parser.add_argument("--reject", metavar="IDENTIFIER", help="Reject investigator by username, user ID, or badge ID")
    parser.add_argument("--reason", default="Administrative decision", help="Reason for rejection")
    parser.add_argument("--suspend", metavar="IDENTIFIER", help="Suspend an investigator account")
    parser.add_argument("--pending", metavar="IDENTIFIER", help="Reset an investigator to pending status")

    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.list:
            list_investigators(db)
        elif args.approve:
            approve_investigator(db, args.approve)
        elif args.approve_all:
            approve_all_pending(db)
        elif args.reject:
            reject_investigator(db, args.reject, args.reason)
        elif args.suspend:
            suspend_investigator(db, args.suspend, args.reason)
        elif args.pending:
            set_pending_investigator(db, args.pending)
        else:
            list_investigators(db)
            print("Tip: Run with --help to see all commands, or run:")
            print("     python scripts/manage_investigators.py --approve <username>")
    finally:
        db.close()


if __name__ == "__main__":
    main()
