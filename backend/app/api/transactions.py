from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Transaction, User
from app.database.schemas import TransactionResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])

from sqlalchemy import or_, func
from app.database.models import Transaction, User, Case

@router.get("/case/{case_id}", response_model=List[TransactionResponse])
def get_case_transactions(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    txs = db.query(Transaction).filter(Transaction.case_id == case_id).order_by(Transaction.block_timestamp.desc()).all()
    if not txs and case and case.suspect_wallet:
        norm_sw = case.suspect_wallet.lower().strip()
        txs = db.query(Transaction).filter(
            or_(
                func.lower(Transaction.from_address) == norm_sw,
                func.lower(Transaction.to_address) == norm_sw
            )
        ).order_by(Transaction.block_timestamp.desc()).all()
    return txs

@router.get("/{tx_hash}")
def get_transaction_by_hash(
    tx_hash: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves transaction data by hash using database-first caching.
    If not cached, queries Ethereum Sepolia on-chain, normalizes, stores, and returns.
    Returns HTTP 404 if transaction is not found.
    """
    import re
    from fastapi.responses import JSONResponse
    from app.services.transaction_service import TransactionService

    clean_hash = tx_hash.strip()
    result = TransactionService.get_transaction_by_hash(db, clean_hash)
    if result:
        return result

    if not re.match(r"^0x[a-fA-F0-9]{64}$", clean_hash):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid transaction hash", "detail": "Transaction hash must be a 66-character hexadecimal string starting with 0x"}
        )

    return JSONResponse(
        status_code=404,
        content={"error": "Transaction not found", "detail": "Transaction not found"}
    )
