import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class RiskFactorContribution(BaseModel):
    factor: str
    points: float
    explanation: str
    supporting_transactions: List[str] = Field(default_factory=list)
    supporting_wallets: List[str] = Field(default_factory=list)

class MLOutput(BaseModel):
    model_available: bool = False
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    prediction: Optional[str] = None
    ml_risk_probability: Optional[float] = None
    feature_importance: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: List[str] = Field(default_factory=list)
    reason: Optional[str] = None
    rule_based_risk_available: bool = True

class InvestigationRiskResponse(BaseModel):
    wallet_address: str
    case_id: Optional[str] = None
    blockchain: str = "Ethereum"
    chain_id: int = 11155111
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_category: str  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    rule_based_score: float
    contributions: List[RiskFactorContribution] = Field(default_factory=list)
    patterns_detected: List[str] = Field(default_factory=list)
    ml: MLOutput = Field(default_factory=MLOutput)
    evidence: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "Analytical Prioritization Notice: This investigation risk score reflects observed transaction "
        "and topological patterns. It does NOT establish guilt or legal proof of fraud."
    )
    assessed_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class CaseRiskResponse(BaseModel):
    case_id: str
    suspect_wallet: str
    blockchain: str = "Ethereum"
    risk_score: float
    risk_category: str
    contributions: List[RiskFactorContribution] = Field(default_factory=list)
    patterns_detected: List[str] = Field(default_factory=list)
    ml: MLOutput = Field(default_factory=MLOutput)
    assessed_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
