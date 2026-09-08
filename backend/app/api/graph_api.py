import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.graph.graph_service import GraphService
from app.graph.graph_models import (
    GraphResponse,
    PathDiscoveryResponse,
    CounterpartiesResponse
)

logger = logging.getLogger("api.graph")
router = APIRouter(tags=["Graph & Tracing"])

@router.get("/graph/wallet/{address}", response_model=GraphResponse)
def get_wallet_graph(
    address: str,
    max_hops: int = Query(3, ge=1, le=5, description="Tracing depth (1 to 5 hops, default 3)"),
    direction: str = Query("both", pattern="^(incoming|outgoing|both)$", description="Fund flow direction"),
    min_value: Optional[float] = Query(None, ge=0.0, description="Minimum transaction value in ETH"),
    max_value: Optional[float] = Query(None, ge=0.0, description="Maximum transaction value in ETH"),
    from_block: Optional[int] = Query(None, ge=0, description="Starting block number filter"),
    to_block: Optional[int] = Query(None, ge=0, description="Ending block number filter"),
    start_timestamp: Optional[str] = Query(None, description="ISO timestamp start filter"),
    end_timestamp: Optional[str] = Query(None, description="ISO timestamp end filter"),
    db: Session = Depends(get_db)
):
    """
    Generates a multi-hop directed transaction graph for a suspect wallet using stored PostgreSQL records.
    Wallets = Nodes, Transactions = Directed Edges (from -> to).
    """
    if not GraphService.validate_wallet_address(address):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid Ethereum wallet address", "detail": "Must be a 42-character hexadecimal string starting with 0x"}
        )

    try:
        graph = GraphService.build_wallet_graph(
            db=db,
            wallet_address=address,
            max_hops=max_hops,
            direction=direction,
            min_value=min_value,
            max_value=max_value,
            from_block=from_block,
            to_block=to_block,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp
        )
        return graph
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"error": str(ve)})
    except Exception as e:
        logger.error(f"Error building graph for {address}: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal database error processing graph"})

@router.get("/graph/paths/{address}", response_model=PathDiscoveryResponse)
def get_wallet_paths(
    address: str,
    max_hops: int = Query(3, ge=1, le=5, description="Maximum traversal depth (1 to 5 hops)"),
    direction: str = Query("both", pattern="^(incoming|outgoing|both)$", description="Fund flow direction"),
    min_value: Optional[float] = Query(None, ge=0.0, description="Minimum transaction value in ETH filter"),
    db: Session = Depends(get_db)
):
    """
    Discovers directed money-flow paths within the specified hop depth.
    """
    if not GraphService.validate_wallet_address(address):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid Ethereum wallet address", "detail": "Must be a 42-character hexadecimal string starting with 0x"}
        )

    try:
        paths = GraphService.get_wallet_paths(
            db=db,
            wallet_address=address,
            max_hops=max_hops,
            direction=direction,
            min_value=min_value
        )
        return paths
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"error": str(ve)})
    except Exception as e:
        logger.error(f"Error discovering paths for {address}: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal database error discovering paths"})

@router.get("/wallets/{address}/counterparties", response_model=CounterpartiesResponse)
def get_wallet_counterparties(
    address: str,
    db: Session = Depends(get_db)
):
    """
    Returns direct 1-hop counterparties (incoming senders and outgoing recipients) from stored transactions.
    """
    if not GraphService.validate_wallet_address(address):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid Ethereum wallet address", "detail": "Must be a 42-character hexadecimal string starting with 0x"}
        )

    try:
        counterparties = GraphService.get_wallet_counterparties(
            db=db,
            wallet_address=address
        )
        return counterparties
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"error": str(ve)})
    except Exception as e:
        logger.error(f"Error fetching counterparties for {address}: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal database error fetching counterparties"})

@router.get("/cases/{case_id}/graph", response_model=GraphResponse)
def get_case_graph(
    case_id: str,
    max_hops: int = Query(3, ge=1, le=5, description="Tracing depth (1 to 5 hops, default 3)"),
    direction: str = Query("both", pattern="^(incoming|outgoing|both)$"),
    min_value: Optional[float] = Query(None, ge=0.0),
    max_value: Optional[float] = Query(None, ge=0.0),
    from_block: Optional[int] = Query(None, ge=0),
    to_block: Optional[int] = Query(None, ge=0),
    db: Session = Depends(get_db)
):
    """
    Builds the transaction graph directly from a case's associated suspect wallet.
    """
    try:
        return GraphService.get_case_graph(
            db=db,
            case_id=case_id,
            max_hops=max_hops,
            direction=direction,
            min_value=min_value,
            max_value=max_value,
            from_block=from_block,
            to_block=to_block
        )
    except ValueError as ve:
        msg = str(ve)
        status_code = 404 if "not found" in msg.lower() else 400
        return JSONResponse(status_code=status_code, content={"error": msg})
    except Exception as e:
        logger.error(f"Error generating graph for case {case_id}: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal database error processing case graph"})
