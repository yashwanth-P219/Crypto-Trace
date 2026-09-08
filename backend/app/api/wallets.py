from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User, Wallet, Transaction, AddressLabel
from app.database.schemas import WalletAnalysisRequest, TransactionResponse
from app.api.auth import get_current_user
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/wallets", tags=["Wallet Forensics"])

@router.post("/analyze")
def analyze_wallet(
    req: WalletAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return WalletService.analyze_wallet(
            db=db,
            address=req.address,
            blockchain=req.blockchain,
            hops=req.hops,
            case_id=req.case_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@router.get("/{address}/balance")
def get_wallet_balance(address: str):
    """
    Retrieves real Ethereum Sepolia balance for the given wallet address.
    Returns HTTP 400 if the address is invalid.
    """
    from app.blockchain.ethereum import EthereumProvider
    from fastapi.responses import JSONResponse
    provider = EthereumProvider(network="Sepolia")
    
    if not provider.validate_address(address):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid Ethereum wallet address"}
        )
    try:
        return provider.get_balance(address)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid Ethereum wallet address"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"RPC Error fetching balance: {str(e)}"}
        )

@router.get("/{address}")
def get_wallet(address: str):
    """
    Retrieves wallet information and Sepolia balance.
    """
    return get_wallet_balance(address)

@router.get("/{address}/validate")
def validate_wallet_address(address: str):
    """
    Validates EVM/Ethereum address format.
    """
    from app.services.transaction_service import TransactionService
    is_valid = TransactionService.validate_wallet_address(address)
    return {
        "address": address,
        "is_valid": is_valid,
        "blockchain": "Ethereum",
        "chain_id": 11155111
    }

@router.get("/{address}/transactions")
def get_wallet_transactions(
    address: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    direction: str = Query("all", pattern="^(incoming|outgoing|all)$"),
    from_block: Optional[int] = None,
    to_block: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieves stored paginated transactions for a wallet from the database.
    Supports direction filtering (incoming, outgoing, all) and block range.
    """
    from fastapi.responses import JSONResponse
    from app.services.transaction_service import TransactionService

    try:
        return TransactionService.get_wallet_transactions(
            db=db,
            address=address,
            page=page,
            page_size=page_size,
            direction=direction,
            from_block=from_block,
            to_block=to_block
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to retrieve transactions: {str(e)}"}
        )

@router.post("/{address}/transactions/sync")
def sync_wallet_transactions(
    address: str,
    case_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Synchronizes on-chain transactions for a wallet from Ethereum Sepolia into PostgreSQL.
    Prevents duplicate transactions via unique constraint.
    """
    from fastapi.responses import JSONResponse
    from app.services.transaction_service import TransactionService

    try:
        return TransactionService.sync_wallet_transactions(
            db=db,
            address=address,
            case_id=case_id
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to synchronize transactions: {str(e)}"}
        )
