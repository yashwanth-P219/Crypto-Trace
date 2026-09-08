import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class AddressLabelCreate(BaseModel):
    address: str
    blockchain: str = "Ethereum"
    chain_id: int = 11155111
    entity_type: str = "UNKNOWN"
    entity_name: str
    label: Optional[str] = None
    source: Optional[str] = "Forensic Database"
    source_url: Optional[str] = None
    confidence: str = "HIGH"  # "HIGH" | "MEDIUM" | "LOW"
    verified: bool = False
    notes: Optional[str] = None

class AddressLabelResponse(BaseModel):
    id: int
    address: str
    blockchain: str
    chain_id: int
    entity_type: str
    entity_name: str
    label: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    confidence: str
    verified: bool
    last_verified_at: Optional[datetime.datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

class EntityResolveResponse(BaseModel):
    address: str
    blockchain: str = "Ethereum"
    chain_id: int = 11155111
    entity_type: str = "UNKNOWN"
    entity_name: Optional[str] = None
    label: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    confidence: str = "LOW"
    verified: bool = False
    is_known: bool = False

class LabelImportItem(BaseModel):
    address: str
    blockchain: str = "Ethereum"
    chain_id: int = 11155111
    entity_type: str
    entity_name: str
    label: Optional[str] = None
    source: Optional[str] = "Dataset Import"
    source_url: Optional[str] = None
    confidence: str = "HIGH"
    verified: bool = False
    notes: Optional[str] = None

class LabelImportRequest(BaseModel):
    labels: List[LabelImportItem]
    dataset_name: Optional[str] = "Manual Import"

class LabelImportResponse(BaseModel):
    imported_count: int
    skipped_duplicates: int
    failed_count: int
    errors: List[str] = Field(default_factory=list)
