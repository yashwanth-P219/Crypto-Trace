from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import (
    UserRole, CaseStatus, CasePriority, EntityType,
    ConfidenceLevel, FindingSeverity, ReportStatus
)

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    badge_number: Optional[str] = None
    phone_number: Optional[str] = None
    role: UserRole = UserRole.INVESTIGATOR

class UserCreate(UserBase):
    password: str

class UserRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    phone_number: Optional[str] = None
    role: UserRole = UserRole.VICTIM
    # Investigator specific fields
    organization: Optional[str] = None
    department: Optional[str] = None
    experience_years: Optional[int] = 0
    specialization: Optional[str] = None
    badge_number: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    investigator_approval_status: Optional[str] = None

class LoginRequest(BaseModel):
    username: str  # Can be username, email, or phone
    password: str

# Investigator Schemas
class InvestigatorProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    phone_number: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    experience_years: int = 0
    specialization: Optional[str] = None
    badge_id: Optional[str] = None
    approval_status: str
    availability_status: str
    rejection_reason: Optional[str] = None
    active_cases_count: int = 0
    created_at: datetime

class AvailableInvestigator(BaseModel):
    id: int
    full_name: str
    username: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    experience_years: int = 0
    specialization: Optional[str] = None
    availability_status: str = "AVAILABLE"
    active_cases_count: int = 0

class InvestigatorApprovalAction(BaseModel):
    rejection_reason: Optional[str] = None

class InvestigatorAvailabilityUpdate(BaseModel):
    availability_status: str  # "AVAILABLE" | "BUSY" | "OFFLINE"

# Case Schemas
class CaseCreate(BaseModel):
    title: Optional[str] = None
    victim_name: Optional[str] = None
    complaint_reference: Optional[str] = None
    amount_lost: float
    currency: str = "INR"
    incident_date: Optional[datetime] = None
    description: Optional[str] = None
    suspect_wallet: Optional[str] = None
    blockchain: str = "Ethereum"
    transaction_hash: Optional[str] = None
    priority: CasePriority = CasePriority.HIGH
    preferred_investigator_id: Optional[int] = None
    investigator_id: Optional[int] = None
    evidence_type: Optional[str] = "wallet"

class ComplaintCreateRequest(BaseModel):
    evidence_type: str = "wallet"  # "wallet" | "tx_hash" | "both" | "none"
    title: Optional[str] = None
    victim_name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    incident_description: Optional[str] = None
    amount_lost: float
    currency: str = "INR"
    incident_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    exchange_used: Optional[str] = None
    suspect_wallet: Optional[str] = None
    transaction_hash: Optional[str] = None
    blockchain: str = "Ethereum"
    sender_wallet: Optional[str] = None
    recipient_wallet: Optional[str] = None
    priority: Optional[CasePriority] = CasePriority.HIGH
    preferred_investigator_id: Optional[int] = None
    evidence_files: Optional[List[Dict[str, Any]]] = None

class CaseUpdate(BaseModel):
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None
    assigned_investigator_id: Optional[int] = None
    description: Optional[str] = None
    suspect_wallet: Optional[str] = None
    transaction_hash: Optional[str] = None

class CaseAssignmentResponse(BaseModel):
    id: int
    case_id: str
    case_number: Optional[str] = None
    victim_id: Optional[int] = None
    investigator_id: int
    investigator_name: Optional[str] = None
    status: str
    assigned_at: datetime
    accepted_at: Optional[datetime] = None
    notes: Optional[str] = None

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    case_id: Optional[str] = None
    notification_type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

class NotificationUnreadCountResponse(BaseModel):
    unread_count: int

class InvestigationRecommendation(BaseModel):
    id: str
    recommendation_type: str
    title: str
    description: str
    priority: str
    target_address: Optional[str] = None
    target_tx: Optional[str] = None
    reasoning: List[str] = []
    suggested_action: str

class CaseRecommendationsResponse(BaseModel):
    case_id: str
    total_recommendations: int
    recommendations: List[InvestigationRecommendation]

class CaseResponse(BaseModel):
    case_id: str
    case_number: Optional[str] = None
    title: Optional[str] = None
    victim_id: Optional[int] = None
    victim_name: str
    complaint_reference: str
    amount_lost: float
    currency: str
    incident_date: datetime
    description: Optional[str] = None
    suspect_wallet: Optional[str] = None
    blockchain: str
    transaction_hash: Optional[str] = None
    status: CaseStatus
    priority: CasePriority
    created_at: datetime
    updated_at: datetime
    assigned_investigator_id: Optional[int] = None
    assigned_investigator: Optional[UserResponse] = None

    class Config:
        from_attributes = True

# Wallet Schemas
class WalletBase(BaseModel):
    address: str
    blockchain: str = "Ethereum"
    label: Optional[str] = None
    entity_type: EntityType = EntityType.UNKNOWN
    risk_score: float = 0.0
    risk_level: str = "LOW"
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    total_incoming: float = 0.0
    total_outgoing: float = 0.0
    tx_count: int = 0

class WalletResponse(WalletBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WalletAnalysisRequest(BaseModel):
    address: str
    blockchain: str = "Ethereum"
    hops: int = Field(default=2, ge=1, le=5)
    case_id: Optional[str] = None

# Transaction Schemas
class TransactionResponse(BaseModel):
    transaction_hash: str
    blockchain: str
    block_number: Optional[int] = None
    timestamp: Optional[datetime] = None
    from_address: str
    to_address: Optional[str] = None
    amount_native: float
    amount_usd_if_available: Optional[float] = None
    gas_used: Optional[float] = None
    gas_fee: Optional[float] = None
    status: str
    case_id: Optional[str] = None

    class Config:
        from_attributes = True

class PaginatedTransactionsResponse(BaseModel):
    wallet: str
    blockchain: str
    chain_id: int
    page: int
    page_size: int
    total: int
    transactions: List[Dict[str, Any]]

class TransactionSyncResponse(BaseModel):
    wallet: str
    blockchain: str
    chain_id: int
    fetched: int
    inserted: int
    updated: int
    duplicates: int
    failed: int

# Address Label Schemas
class AddressLabelCreate(BaseModel):
    address: str
    blockchain: str = "Ethereum"
    entity_name: str
    entity_type: EntityType
    source: str = "Manual Admin Entry"
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    notes: Optional[str] = None

class AddressLabelResponse(BaseModel):
    id: int
    address: str
    blockchain: str
    entity_name: str
    entity_type: EntityType
    source: str
    confidence: ConfidenceLevel
    last_verified: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True

# Risk & Patterns Schemas
class RiskFindingResponse(BaseModel):
    id: int
    case_id: str
    wallet_address: str
    finding_type: str
    severity: FindingSeverity
    score_delta: float
    evidence_txs: List[str] = []
    explanation: str
    created_at: datetime

    class Config:
        from_attributes = True

class RiskAssessmentResponse(BaseModel):
    wallet_address: str
    blockchain: str
    risk_score: float
    risk_level: str
    reasons: List[Dict[str, Any]]
    findings: List[RiskFindingResponse]
    metrics: Dict[str, Any]

# Evidence Schemas
class EvidenceCreate(BaseModel):
    case_id: str
    blockchain: str = "Ethereum"
    wallet: str
    transaction_hash: str
    block_number: Optional[int] = None
    timestamp: Optional[datetime] = None
    from_address: str
    to_address: str
    amount: float
    finding_type: Optional[str] = None
    tag: str = "SUSPICIOUS"
    source: str = "Blockchain Verification"
    investigator_notes: Optional[str] = None
    importance: str = "HIGH"

class EvidenceResponse(BaseModel):
    evidence_id: str
    case_id: str
    blockchain: str
    wallet: str
    transaction_hash: str
    block_number: Optional[int] = None
    timestamp: Optional[datetime] = None
    from_address: str
    to_address: str
    amount: float
    finding_type: Optional[str] = None
    tag: str
    source: str
    retrieved_at: datetime
    investigator_notes: Optional[str] = None
    importance: str
    integrity_hash: str

    class Config:
        from_attributes = True

# Monitoring Schemas
class MonitoringCreate(BaseModel):
    case_id: str
    wallet_address: str
    blockchain: str = "Ethereum"
    label: Optional[str] = None

class AlertResponse(BaseModel):
    id: int
    monitoring_id: int
    wallet_address: str
    tx_hash: Optional[str] = None
    risk_level: str
    reason: str
    timestamp: datetime
    is_read: bool

    class Config:
        from_attributes = True

class AlertStatusUpdate(BaseModel):
    is_read: bool = True

class AlertRuleCreate(BaseModel):
    case_id: Optional[str] = None
    rule_name: str
    rule_type: str  # "LARGE_TRANSACTION", "SUSPICIOUS_PATTERN", "KNOWN_VASP_INTERACTION", "RISK_THRESHOLD", "NEW_COUNTERPARTY"
    threshold_value: float = 0.0
    is_active: bool = True

class AlertRuleResponse(BaseModel):
    id: int
    case_id: Optional[str] = None
    rule_name: str
    rule_type: str
    threshold_value: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class MonitoringResponse(BaseModel):
    id: int
    case_id: str
    wallet_address: str
    blockchain: str
    label: Optional[str] = None
    is_active: bool
    created_at: datetime
    alerts: List[AlertResponse] = []

    class Config:
        from_attributes = True

# Report Schemas
class ReportCreate(BaseModel):
    case_id: str
    title: Optional[str] = None

class ReportReview(BaseModel):
    status: ReportStatus
    supervisor_comments: Optional[str] = None

class ReportResponse(BaseModel):
    report_id: str
    case_id: str
    title: str
    content_json: Dict[str, Any]
    status: ReportStatus
    supervisor_id: Optional[int] = None
    supervisor_comments: Optional[str] = None
    generated_at: datetime
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: str
    action: str
    case_id: Optional[str] = None
    timestamp: datetime
    metadata_json: Dict[str, Any]

    class Config:
        from_attributes = True

# Copilot Schemas
class CopilotQueryRequest(BaseModel):
    case_id: str
    question: str

class CopilotQueryResponse(BaseModel):
    question: str
    answer: str
    grounded_evidence: List[Dict[str, Any]]
    confidence: str = "HIGH"
    category: str = "SYSTEM INFERENCE"

# Investigator Note Schemas
class NoteCreate(BaseModel):
    case_id: str
    content: str

class NoteResponse(BaseModel):
    id: int
    case_id: str
    author_id: int
    author_name: Optional[str] = None
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
