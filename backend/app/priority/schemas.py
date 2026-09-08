import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PriorityItemBase(BaseModel):
    object_type: str = "WALLET"  # "WALLET", "TRANSACTION", "PATTERN", "PATH", "ENTITY", "CASE"
    object_id: str
    wallet_address: Optional[str] = None
    blockchain: str = "Ethereum"
    chain_id: int = 11155111
    priority_score: float = Field(default=0.0, ge=0.0, le=100.0)
    priority_category: str = "LOW"  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    risk_score: Optional[float] = None
    reasons: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    case_id: Optional[str] = None
    assigned_to: Optional[str] = None
    status: str = "NEW"  # "NEW", "REVIEWED", "IMPORTANT", "DISMISSED"
    notes: Optional[str] = None

class PriorityItemResponse(PriorityItemBase):
    id: Optional[int] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

class PriorityQueueResponse(BaseModel):
    total_leads: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    queue: List[PriorityItemResponse]

class LeadReviewRequest(BaseModel):
    status: str = "REVIEWED"  # "REVIEWED", "IMPORTANT", "DISMISSED"
    notes: Optional[str] = None

class LeadAssignRequest(BaseModel):
    assigned_to: str

class LeadNoteRequest(BaseModel):
    note: str

class PriorityCalculationRequest(BaseModel):
    wallet_address: str
    case_id: Optional[str] = None
    chain_id: Optional[int] = 11155111

