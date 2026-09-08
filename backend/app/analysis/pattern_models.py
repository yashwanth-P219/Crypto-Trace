import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class PatternFinding(BaseModel):
    pattern_id: str
    pattern_name: str
    severity: str = "MEDIUM"  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    confidence: float = 1.0   # 0.0 to 1.0
    description: str
    wallet_address: str
    related_wallets: List[str] = Field(default_factory=list)
    related_transaction_hashes: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class PatternAnalysisResponse(BaseModel):
    wallet_address: str
    blockchain: str = "Ethereum"
    chain_id: int = 11155111
    case_id: Optional[str] = None
    total_patterns_detected: int = 0
    patterns: List[PatternFinding] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    analyzed_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class CasePatternsResponse(BaseModel):
    case_id: str
    suspect_wallet: Optional[str] = None
    blockchain: str = "Ethereum"
    total_patterns_detected: int = 0
    patterns: List[PatternFinding] = Field(default_factory=list)
    analyzed_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
