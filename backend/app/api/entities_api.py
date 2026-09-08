from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from web3 import Web3
from app.database.database import get_db
from app.database.models import User, UserRole
from app.api.auth import get_current_user, require_roles
from app.entities.schemas import (
    AddressLabelCreate, AddressLabelResponse, EntityResolveResponse,
    LabelImportRequest, LabelImportResponse
)
from app.entities.repository import AddressLabelRepository
from app.entities.resolver import EntityResolver
from app.entities.service import EntityService

router = APIRouter(prefix="/entities", tags=["Wallet & VASP Entity Identification"])

@router.get("/address/{address}", response_model=EntityResolveResponse)
def resolve_entity_address(
    address: str,
    blockchain: str = Query(default="Ethereum"),
    chain_id: int = Query(default=11155111),
    db: Session = Depends(get_db)
):
    """
    Identifies a known exchange, VASP, mixer, or service from an Ethereum address.
    Unlabeled addresses strictly resolve to UNKNOWN (unknown does not imply fraud).
    """
    if not Web3.is_address(address):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid wallet address format: '{address}'. Must be a valid 0x Ethereum address."
        )

    return EntityResolver.resolve_address(
        db=db,
        address=address,
        blockchain=blockchain,
        chain_id=chain_id
    )

@router.get("/case/{case_id}", response_model=List[EntityResolveResponse])
def get_case_entities(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns resolved entity identities for all addresses participating in a case.
    """
    try:
        return EntityService.get_case_entities(db=db, case_id=case_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Case entity resolution failed: {str(e)}")

@router.post("/labels", response_model=AddressLabelResponse)
def create_or_update_label(
    label_in: AddressLabelCreate,
    db: Session = Depends(get_db)
):
    """
    Creates or updates an intelligence label for a known cryptocurrency address.
    """
    try:
        return EntityService.create_or_update_label(db=db, label_in=label_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save label: {str(e)}")

@router.post("/import", response_model=LabelImportResponse)
def import_labels_dataset(
    import_req: LabelImportRequest,
    db: Session = Depends(get_db)
):
    """
    Batch imports validated address labels from a dataset (CSV / JSON formatted).
    """
    try:
        return EntityService.import_labels(db=db, import_req=import_req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dataset import failed: {str(e)}")

@router.get("/search", response_model=List[AddressLabelResponse])
def search_entities(
    q: str = Query(..., min_length=2, description="Search query for name, label, or address"),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Searches the intelligence directory for matching known entities or addresses.
    """
    return AddressLabelRepository.search_labels(db=db, query_str=q, limit=limit)

@router.post("/seed-demo")
def seed_demo_intel(db: Session = Depends(get_db)):
    """
    Seeds standard demo VASP / exchange / mixer labels (explicitly marked as DEMO DATASET).
    """
    count = EntityService.seed_demo_intel(db=db)
    return {"status": "success", "seeded_count": count}
