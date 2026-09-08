import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from web3 import Web3
from pydantic import BaseModel, Field

from app.database.database import get_db
from app.database.models import Case
from app.analysis.pattern_service import PatternService
from app.analysis.pattern_models import PatternFinding
from app.risk.risk_service import RiskService
from app.risk.schemas import RiskFactorContribution, InvestigationRiskResponse
from app.risk.explainability import RiskExplainability
from app.entities.resolver import EntityResolver
from app.entities.schemas import EntityResolveResponse

router = APIRouter(tags=["Combined Forensic Investigation"])

class CombinedInvestigationResponse(BaseModel):
    wallet_address: str
    case_id: Optional[str] = None
    blockchain: str = "Ethereum"
    chain_id: int = 11155111
    risk_score: float
    risk_category: str
    rule_based_score: float
    why_this_risk: List[str] = Field(default_factory=list)
    contributions: List[RiskFactorContribution] = Field(default_factory=list)
    patterns: List[PatternFinding] = Field(default_factory=list)
    entities_identified: List[EntityResolveResponse] = Field(default_factory=list)
    evidence_transactions: List[str] = Field(default_factory=list)
    ml_summary: Optional[Dict[str, Any]] = None
    summary_verdict: str
    disclaimer: str = (
        "Forensic Investigation Notice: This assessment provides structured investigative leads "
        "and analytical pattern correlations. It does not constitute legal proof or definitive attribution."
    )
    analyzed_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

@router.get("/investigation/wallet/{address}/analysis", response_model=CombinedInvestigationResponse)
def get_wallet_investigation_analysis(
    address: str,
    case_id: Optional[str] = None,
    max_hops: int = Query(default=3, ge=1, le=5),
    blockchain: str = Query(default="Ethereum"),
    chain_id: int = Query(default=11155111),
    db: Session = Depends(get_db)
):
    """
    Executes the complete combined investigative pipeline:
    Transactions -> Graph -> Patterns (Phase 5) -> Risk Scoring & Explainability (Phase 6) -> Entity Identification (Phase 7) -> Consolidated Dossier.
    """
    if hasattr(chain_id, "default"):
        chain_id = chain_id.default
    if hasattr(max_hops, "default"):
        max_hops = max_hops.default
    if hasattr(blockchain, "default"):
        blockchain = blockchain.default

    if not Web3.is_address(address):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid wallet address format: '{address}'. Must be a valid 0x Ethereum address."
        )

    norm_wallet = address.lower()

    try:
        # 1. Evaluate patterns
        pattern_res = PatternService.analyze_wallet_patterns(
            db=db,
            wallet_address=norm_wallet,
            case_id=case_id,
            max_hops=max_hops,
            blockchain=blockchain,
            chain_id=chain_id,
            persist=True
        )

        # 2. Evaluate risk & ML
        risk_res = RiskService.assess_wallet_risk(
            db=db,
            wallet_address=norm_wallet,
            case_id=case_id,
            blockchain=blockchain,
            chain_id=chain_id,
            max_hops=max_hops,
            persist=True
        )

        # 3. Resolve all related counterparties into entities
        related_addrs = set([norm_wallet])
        for p in pattern_res.patterns:
            for w in p.related_wallets:
                related_addrs.add(w.lower())

        entities = []
        for a in list(related_addrs)[:25]:
            resolved = EntityResolver.resolve_address(db, a, blockchain, chain_id)
            if resolved.is_known:
                entities.append(resolved)

        # 4. Generate "Why this risk?" explanations
        why_risk = RiskExplainability.generate_why_this_risk(
            contributions=risk_res.contributions,
            risk_category=risk_res.risk_category
        )

        # 5. Formulate neutral summary verdict
        if risk_res.risk_score >= 75.0:
            verdict = "CRITICAL: Multiple high-confidence layering, dispersion, or liquidation patterns detected requiring urgent investigation."
        elif risk_res.risk_score >= 50.0:
            verdict = "HIGH: Significant behavioral patterns identified indicating potential mule routing or structuring activity."
        elif risk_res.risk_score >= 25.0:
            verdict = "MEDIUM: Moderate pattern indicators observed; counterparties and timing warrant investigator review."
        else:
            verdict = "LOW: Baseline transaction behavior observed with minimal anomalous indicators in indexed history."

        ml_dict = None
        if risk_res.ml.model_available:
            ml_dict = {
                "model_name": risk_res.ml.model_name,
                "model_version": risk_res.ml.model_version,
                "prediction": risk_res.ml.prediction,
                "ml_risk_probability": risk_res.ml.ml_risk_probability,
                "feature_importance": risk_res.ml.feature_importance[:3]
            }

        return CombinedInvestigationResponse(
            wallet_address=norm_wallet,
            case_id=case_id,
            blockchain=blockchain,
            chain_id=chain_id,
            risk_score=risk_res.risk_score,
            risk_category=risk_res.risk_category,
            rule_based_score=risk_res.rule_based_score,
            why_this_risk=why_risk,
            contributions=risk_res.contributions,
            patterns=pattern_res.patterns,
            entities_identified=entities,
            evidence_transactions=risk_res.evidence,
            ml_summary=ml_dict,
            summary_verdict=verdict,
            analyzed_at=datetime.datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investigation analysis failed: {str(e)}")

@router.get("/cases/{case_id}/analysis", response_model=CombinedInvestigationResponse)
def get_case_investigation_analysis(
    case_id: str,
    max_hops: int = Query(default=3, ge=1, le=5),
    db: Session = Depends(get_db)
):
    """
    Executes combined investigation analysis for a specific registered case.
    """
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    return get_wallet_investigation_analysis(
        address=case.suspect_wallet,
        case_id=case_id,
        max_hops=max_hops,
        blockchain=case.blockchain or "Ethereum",
        chain_id=11155111,
        db=db
    )
