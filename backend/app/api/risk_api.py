from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from web3 import Web3
from app.database.database import get_db
from app.risk.risk_service import RiskService
from app.risk.schemas import InvestigationRiskResponse, CaseRiskResponse

router = APIRouter(prefix="/risk", tags=["Risk Engine & Explainable ML"])

@router.get("/wallet/{address}", response_model=InvestigationRiskResponse)
def get_wallet_risk(
    address: str,
    max_hops: int = Query(default=3, ge=1, le=5),
    blockchain: str = Query(default="Ethereum"),
    chain_id: int = Query(default=11155111),
    db: Session = Depends(get_db)
):
    """
    Computes an explainable 0-100 investigation risk score based on transparent rule scoring,
    topological money flows, and optional modular machine learning.
    """
    if not Web3.is_address(address):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid wallet address format: '{address}'. Must be a valid 0x Ethereum address."
        )

    try:
        return RiskService.assess_wallet_risk(
            db=db,
            wallet_address=address,
            max_hops=max_hops,
            blockchain=blockchain,
            chain_id=chain_id,
            persist=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")

@router.get("/case/{case_id}", response_model=CaseRiskResponse)
def get_case_risk(
    case_id: str,
    max_hops: int = Query(default=3, ge=1, le=5),
    db: Session = Depends(get_db)
):
    """
    Evaluates investigation risk across all transactions and wallets linked to a case.
    """
    try:
        return RiskService.assess_case_risk(
            db=db,
            case_id=case_id,
            max_hops=max_hops
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Case risk assessment failed: {str(e)}")
