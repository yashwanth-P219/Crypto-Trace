from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from web3 import Web3
from app.database.database import get_db
from app.analysis.pattern_service import PatternService
from app.analysis.pattern_models import PatternAnalysisResponse, CasePatternsResponse

router = APIRouter(prefix="/analysis", tags=["Suspicious Pattern Detection"])

@router.get("/wallet/{address}/patterns", response_model=PatternAnalysisResponse)
def get_wallet_patterns(
    address: str,
    max_hops: int = Query(default=3, ge=1, le=5, description="Hop depth for multi-hop pattern detection"),
    blockchain: str = Query(default="Ethereum"),
    chain_id: int = Query(default=11155111),
    db: Session = Depends(get_db)
):
    """
    Analyzes transaction behavior and multi-hop flows for a suspect wallet and
    returns detected suspicious patterns (Phase 5) without declaring definitive criminality.
    """
    if not Web3.is_address(address):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid wallet address format: '{address}'. Must be a valid 0x Ethereum address."
        )

    try:
        return PatternService.analyze_wallet_patterns(
            db=db,
            wallet_address=address,
            max_hops=max_hops,
            blockchain=blockchain,
            chain_id=chain_id,
            persist=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern analysis failed: {str(e)}")

@router.get("/case/{case_id}/patterns", response_model=CasePatternsResponse)
def get_case_patterns(
    case_id: str,
    max_hops: int = Query(default=3, ge=1, le=5),
    db: Session = Depends(get_db)
):
    """
    Analyzes transactions and flow paths for all wallets linked to a specific case.
    """
    try:
        return PatternService.analyze_case_patterns(
            db=db,
            case_id=case_id,
            max_hops=max_hops
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Case pattern analysis failed: {str(e)}")
