import enum
import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, Enum, Index, JSON, BigInteger, UniqueConstraint
)
from sqlalchemy.orm import relationship, synonym
from .database import Base

class UserRole(str, enum.Enum):
    VICTIM = "VICTIM"
    INVESTIGATOR = "INVESTIGATOR"
    SUPERVISOR = "SUPERVISOR"
    ADMINISTRATOR = "ADMINISTRATOR"

class InvestigatorApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"

class InvestigatorAvailabilityStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"

class CaseAssignmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    COMPLETED = "COMPLETED"
    REASSIGNED = "REASSIGNED"

class CaseStatus(str, enum.Enum):
    NEW = "NEW"
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    ANALYSIS_RUNNING = "ANALYSIS_RUNNING"
    EVIDENCE_REVIEW = "EVIDENCE_REVIEW"
    REPORT_PENDING = "REPORT_PENDING"
    SUPERVISOR_REVIEW = "SUPERVISOR_REVIEW"
    ON_HOLD = "ON_HOLD"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"

class CasePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class EntityType(str, enum.Enum):
    VASP = "VASP"
    EXCHANGE = "EXCHANGE"
    BRIDGE = "BRIDGE"
    DEX = "DEX"
    MIXER = "MIXER"
    SCAM = "SCAM"
    SCAM_ASSOCIATED = "SCAM_ASSOCIATED"
    KNOWN_SERVICE = "KNOWN_SERVICE"
    SERVICE = "SERVICE"
    PERSONAL_WALLET = "PERSONAL_WALLET"
    SMART_CONTRACT = "SMART_CONTRACT"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"

class ConfidenceLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class FindingSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ReportStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.INVESTIGATOR, nullable=False)
    full_name = Column(String(128), nullable=False)
    badge_number = Column(String(64), nullable=True)
    phone_number = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    cases_assigned = relationship("Case", foreign_keys="[Case.assigned_investigator_id]", back_populates="assigned_investigator")
    cases_reported = relationship("Case", foreign_keys="[Case.victim_id]", back_populates="victim")
    investigator_profile = relationship("InvestigatorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan", foreign_keys="[InvestigatorProfile.user_id]")
    case_assignments = relationship("CaseAssignment", foreign_keys="[CaseAssignment.investigator_id]", back_populates="investigator")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("InvestigatorNote", back_populates="author")
    audit_logs = relationship("AuditLog", back_populates="user")


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String(64), primary_key=True, index=True)
    case_number = Column(String(64), unique=True, index=True, nullable=True)
    title = Column(String(256), nullable=True)
    victim_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    victim_name = Column(String(128), nullable=False)
    complaint_reference = Column(String(64), unique=True, index=True, nullable=False)
    amount_lost = Column(Float, nullable=False)
    currency = Column(String(16), default="INR")
    incident_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=True)
    suspect_wallet = Column(String(128), index=True, nullable=True)
    blockchain = Column(String(32), default="Ethereum", index=True)
    transaction_hash = Column(String(128), nullable=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.NEW, nullable=False)
    priority = Column(Enum(CasePriority), default=CasePriority.HIGH, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    assigned_investigator_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    victim = relationship("User", foreign_keys=[victim_id], back_populates="cases_reported")
    assigned_investigator = relationship("User", foreign_keys=[assigned_investigator_id], back_populates="cases_assigned")
    assignments = relationship("CaseAssignment", back_populates="case", cascade="all, delete-orphan")
    evidence_items = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    notes = relationship("InvestigatorNote", back_populates="case", cascade="all, delete-orphan")
    risk_findings = relationship("RiskFinding", back_populates="case", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="case", cascade="all, delete-orphan")
    monitored_wallets = relationship("Monitoring", back_populates="case", cascade="all, delete-orphan")
    priority_items = relationship("PriorityItem", back_populates="case", cascade="all, delete-orphan")
    timeline_events = relationship("InvestigationTimeline", back_populates="case", cascade="all, delete-orphan")


class Wallet(Base):
    __tablename__ = "wallets"

    address = Column(String(128), primary_key=True, index=True)
    blockchain = Column(String(32), default="Ethereum", primary_key=True, index=True)
    label = Column(String(128), nullable=True)
    entity_type = Column(Enum(EntityType), default=EntityType.UNKNOWN)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(16), default="LOW")
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    total_incoming = Column(Float, default=0.0)
    total_outgoing = Column(Float, default=0.0)
    tx_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(128), index=True, nullable=False)
    blockchain = Column(String(32), default="Ethereum", index=True)
    chain_id = Column(Integer, default=11155111, index=True)
    block_number = Column(Integer, index=True, nullable=True)
    block_hash = Column(String(128), nullable=True)
    transaction_index = Column(Integer, nullable=True)
    from_address = Column(String(128), index=True, nullable=False)
    to_address = Column(String(128), index=True, nullable=True)
    value_wei = Column(String(78), default="0", nullable=False)
    value_eth = Column(Float, default=0.0, nullable=False)
    gas = Column(BigInteger, default=21000)
    gas_price_wei = Column(String(78), nullable=True)
    nonce = Column(Integer, nullable=True)
    receipt_status = Column(String(32), default="SUCCESS")
    gas_used = Column(BigInteger, nullable=True)
    block_timestamp = Column(DateTime, index=True, nullable=True)
    transaction_type = Column(String(32), default="native_transfer")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Optional case association
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=True, index=True)

    # Backward compatibility synonyms and fields
    gas_fee = Column(Float, nullable=True)
    amount_usd_if_available = Column(Float, nullable=True)

    @property
    def transaction_hash(self):
        return self.tx_hash

    @transaction_hash.setter
    def transaction_hash(self, value):
        self.tx_hash = value

    @property
    def amount_native(self):
        return self.value_eth

    @amount_native.setter
    def amount_native(self, value):
        self.value_eth = value

    @property
    def timestamp(self):
        return self.block_timestamp

    @timestamp.setter
    def timestamp(self, value):
        self.block_timestamp = value

    @property
    def status(self):
        return self.receipt_status

    @status.setter
    def status(self, value):
        self.receipt_status = value

    __table_args__ = (
        UniqueConstraint("tx_hash", "blockchain", "chain_id", name="uq_tx_chain"),
        Index("idx_tx_hash_lookup", "tx_hash"),
        Index("idx_from_address_lookup", "from_address"),
        Index("idx_to_address_lookup", "to_address"),
        Index("idx_block_number_lookup", "block_number"),
        Index("idx_blockchain_chain_lookup", "blockchain", "chain_id"),
        Index("idx_block_timestamp_lookup", "block_timestamp"),
    )


class CaseTransaction(Base):
    __tablename__ = "case_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.case_id", ondelete="CASCADE"), index=True, nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("case_id", "transaction_id", name="uq_case_tx"),
    )


class WalletRelationship(Base):
    __tablename__ = "wallet_relationships"

    id = Column(Integer, primary_key=True, index=True)
    from_address = Column(String(128), index=True, nullable=False)
    to_address = Column(String(128), index=True, nullable=False)
    blockchain = Column(String(32), default="Ethereum")
    total_amount = Column(Float, default=0.0)
    transaction_count = Column(Integer, default=1)
    first_timestamp = Column(DateTime, nullable=True)
    last_timestamp = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_relationship_flow", "from_address", "to_address", "blockchain"),
    )


class AddressLabel(Base):
    __tablename__ = "address_labels"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(128), index=True, nullable=False)
    blockchain = Column(String(32), default="Ethereum", index=True, nullable=False)
    chain_id = Column(Integer, default=11155111, nullable=False)
    entity_name = Column(String(128), nullable=False)
    entity_type = Column(Enum(EntityType), default=EntityType.UNKNOWN, nullable=False)
    label = Column(String(256), nullable=True)
    source = Column(String(128), default="Forensic Database")
    source_url = Column(String(512), nullable=True)
    confidence = Column(Enum(ConfidenceLevel), default=ConfidenceLevel.HIGH, nullable=False)
    verified = Column(Boolean, default=False)
    last_verified = Column(DateTime, default=datetime.datetime.utcnow)
    last_verified_at = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        Index("idx_address_label_lookup", "address", "blockchain"),
        Index("idx_address_label_full", "address", "blockchain", "chain_id"),
        UniqueConstraint("address", "blockchain", "chain_id", name="uq_address_blockchain_chain"),
    )


class AnalysisPattern(Base):
    __tablename__ = "analysis_patterns"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=True, index=True)
    wallet_address = Column(String(128), index=True, nullable=False)
    blockchain = Column(String(32), default="Ethereum", index=True, nullable=False)
    chain_id = Column(Integer, default=11155111, nullable=False)
    pattern_id = Column(String(64), index=True, nullable=False)
    pattern_name = Column(String(128), index=True, nullable=False)
    severity = Column(String(16), default="MEDIUM", index=True, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    description = Column(Text, nullable=False)
    related_wallets = Column(JSON, default=list)
    related_transaction_hashes = Column(JSON, default=list)
    evidence_json = Column(JSON, default=dict)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    case = relationship("Case", backref="analysis_patterns")


class RiskAssessmentRecord(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=True, index=True)
    wallet_address = Column(String(128), index=True, nullable=False)
    blockchain = Column(String(32), default="Ethereum", index=True, nullable=False)
    chain_id = Column(Integer, default=11155111, nullable=False)
    risk_score = Column(Float, default=0.0, index=True, nullable=False)
    risk_category = Column(String(16), default="LOW", nullable=False)
    rule_based_score = Column(Float, default=0.0, nullable=False)
    ml_score = Column(Float, nullable=True)
    model_name = Column(String(128), nullable=True)
    model_version = Column(String(32), nullable=True)
    contributions_json = Column(JSON, default=list, nullable=False)
    features_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    case = relationship("Case", backref="risk_assessments")


class RiskFinding(Base):
    __tablename__ = "risk_findings"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=False)
    wallet_address = Column(String(128), index=True, nullable=False)
    finding_type = Column(String(64), nullable=False)
    severity = Column(Enum(FindingSeverity), default=FindingSeverity.MEDIUM)
    score_delta = Column(Float, default=0.0)
    evidence_txs = Column(JSON, default=list)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("Case", back_populates="risk_findings")


class Evidence(Base):
    __tablename__ = "evidence"

    evidence_id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=False)
    blockchain = Column(String(32), default="Ethereum")
    wallet = Column(String(128), nullable=False)
    transaction_hash = Column(String(128), nullable=False, index=True)
    block_number = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=True)
    from_address = Column(String(128), nullable=False)
    to_address = Column(String(128), nullable=False)
    amount = Column(Float, nullable=False)
    finding_type = Column(String(64), nullable=True)
    tag = Column(String(64), default="SUSPICIOUS")
    source = Column(String(64), default="Blockchain Verification")
    retrieved_at = Column(DateTime, default=datetime.datetime.utcnow)
    investigator_notes = Column(Text, nullable=True)
    importance = Column(String(32), default="HIGH")
    integrity_hash = Column(String(128), nullable=False)

    case = relationship("Case", back_populates="evidence_items")


class Monitoring(Base):
    __tablename__ = "monitoring"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=False)
    wallet_address = Column(String(128), index=True, nullable=False)
    blockchain = Column(String(32), default="Ethereum")
    label = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("Case", back_populates="monitored_wallets")
    alerts = relationship("Alert", back_populates="monitoring", cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    monitoring_id = Column(Integer, ForeignKey("monitoring.id"), index=True, nullable=False)
    wallet_address = Column(String(128), index=True, nullable=False)
    tx_hash = Column(String(128), nullable=True)
    risk_level = Column(String(16), default="HIGH")
    reason = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_read = Column(Boolean, default=False)

    monitoring = relationship("Monitoring", back_populates="alerts")


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=False)
    title = Column(String(256), nullable=False)
    content_json = Column(JSON, nullable=False)
    status = Column(Enum(ReportStatus), default=ReportStatus.DRAFT, nullable=False)
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    supervisor_comments = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)

    case = relationship("Case", back_populates="reports")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False, index=True)
    case_id = Column(String(64), index=True, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    metadata_json = Column(JSON, default=dict)

    user = relationship("User", back_populates="audit_logs")


class InvestigatorNote(Base):
    __tablename__ = "investigator_notes"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("Case", back_populates="notes")
    author = relationship("User", back_populates="notes")


class PriorityItem(Base):
    __tablename__ = "priority_items"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    object_type = Column(String(32), nullable=False)  # "WALLET", "TRANSACTION", "PATTERN", "PATH", "ENTITY", "CASE"
    object_id = Column(String(128), nullable=False)
    wallet_address = Column(String(128), index=True, nullable=True)
    blockchain = Column(String(32), default="Ethereum", nullable=False)
    chain_id = Column(Integer, default=11155111, nullable=False)
    priority_score = Column(Float, default=0.0, index=True, nullable=False)
    priority_category = Column(String(16), default="LOW", nullable=False)  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    risk_score = Column(Float, nullable=True)
    reasons = Column(JSON, default=list, nullable=False)
    supporting_evidence = Column(JSON, default=list, nullable=False)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=True)
    assigned_to = Column(String(64), nullable=True)
    status = Column(String(32), default="NEW", nullable=False)  # "NEW", "REVIEWED", "IMPORTANT", "DISMISSED"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    case = relationship("Case", back_populates="priority_items")


class InvestigationTimeline(Base):
    __tablename__ = "investigation_timeline"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=False)
    event_type = Column(String(64), nullable=False)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    actor = Column(String(64), default="SYSTEM", nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    metadata_json = Column(JSON, default=dict)

    case = relationship("Case", back_populates="timeline_events")


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=True)
    rule_name = Column(String(128), nullable=False)
    rule_type = Column(String(64), nullable=False)  # "LARGE_TRANSACTION", "SUSPICIOUS_PATTERN", "KNOWN_VASP_INTERACTION", "RISK_THRESHOLD", "NEW_COUNTERPARTY"
    threshold_value = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("Case")


class CopilotMessage(Base):
    __tablename__ = "copilot_messages"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), index=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role = Column(String(16), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    grounded_evidence = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("Case")
    user = relationship("User")


class BlockchainNetwork(Base):
    __tablename__ = "blockchain_networks"

    chain_id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    symbol = Column(String(16), nullable=False)
    is_active = Column(Boolean, default=True)
    is_evm = Column(Boolean, default=True)
    rpc_url_configured = Column(Boolean, default=False)
    explorer_url = Column(String(256), nullable=True)


class CrossChainLink(Base):
    __tablename__ = "cross_chain_links"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    source_chain_id = Column(Integer, nullable=False)
    destination_chain_id = Column(Integer, nullable=False)
    source_tx_hash = Column(String(128), index=True, nullable=False)
    bridge_contract = Column(String(128), index=True, nullable=False)
    bridge_name = Column(String(128), nullable=False)
    amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class InvestigatorProfile(Base):
    __tablename__ = "investigator_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    organization = Column(String(128), nullable=True)
    department = Column(String(128), nullable=True)
    experience_years = Column(Integer, default=0)
    specialization = Column(String(256), nullable=True)
    badge_id = Column(String(64), nullable=True)
    approval_status = Column(Enum(InvestigatorApprovalStatus), default=InvestigatorApprovalStatus.PENDING, nullable=False, index=True)
    availability_status = Column(Enum(InvestigatorAvailabilityStatus), default=InvestigatorAvailabilityStatus.OFFLINE, nullable=False, index=True)
    rejection_reason = Column(Text, nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id], back_populates="investigator_profile")
    approved_by = relationship("User", foreign_keys=[approved_by_id])


class CaseAssignment(Base):
    __tablename__ = "case_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    victim_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    investigator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Enum(CaseAssignmentStatus), default=CaseAssignmentStatus.PENDING, nullable=False, index=True)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    case = relationship("Case", back_populates="assignments")
    victim = relationship("User", foreign_keys=[victim_id])
    investigator = relationship("User", foreign_keys=[investigator_id], back_populates="case_assignments")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    case_id = Column(String(64), ForeignKey("cases.case_id"), nullable=True, index=True)
    notification_type = Column(String(64), nullable=False)
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    read_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="notifications")
    case = relationship("Case")

