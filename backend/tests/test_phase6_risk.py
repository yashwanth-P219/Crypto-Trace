import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.risk.rules import RuleBasedRiskScorer
from app.risk.features import FeatureExtractor
from app.risk.model import MLRiskClassifier
from app.risk.explainability import RiskExplainability
from app.analysis.pattern_models import PatternFinding

client = TestClient(app)

def test_deterministic_rule_scoring_and_bounds():
    # Construct 6 high-severity findings
    findings = [
        PatternFinding(
            pattern_id="PAT-RAPID-TRANSFER",
            pattern_name="Rapid Fund Transfer",
            severity="HIGH",
            confidence=0.9,
            description="Moved in 2 mins",
            wallet_address="0xwallet",
            related_transaction_hashes=["0xtx1", "0xtx2"]
        ),
        PatternFinding(
            pattern_id="PAT-FUND-SPLITTING",
            pattern_name="Fund Splitting",
            severity="HIGH",
            confidence=0.85,
            description="Split into 5 wallets",
            wallet_address="0xwallet",
            related_transaction_hashes=["0xtx3"]
        ),
        PatternFinding(
            pattern_id="PAT-MULTI-HOP",
            pattern_name="Multi-Hop Movement",
            severity="HIGH",
            confidence=0.85,
            description="Traversed 4 hops",
            wallet_address="0xwallet"
        ),
        PatternFinding(
            pattern_id="PAT-CIRCULAR-FLOW",
            pattern_name="Circular Flow",
            severity="HIGH",
            confidence=0.9,
            description="Loop detected",
            wallet_address="0xwallet"
        ),
        PatternFinding(
            pattern_id="PAT-HIGH-RISK",
            pattern_name="High-Risk Entity",
            severity="CRITICAL",
            confidence=0.95,
            description="Mixer connection",
            wallet_address="0xwallet"
        )
    ]

    res = RuleBasedRiskScorer.calculate_score(findings)
    score = res["risk_score"]

    # Score must be strictly between 0 and 100
    assert 0.0 <= score <= 100.0
    assert res["risk_category"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert len(res["contributions"]) >= 4

    # Factors must have explanations and positive points
    for c in res["contributions"]:
        assert c.points > 0
        assert len(c.explanation) > 0

    # Evidence hashes must be preserved
    assert "0xtx1" in res["evidence_txs"]
    assert "0xtx2" in res["evidence_txs"]

def test_risk_categories():
    # Empty findings -> LOW score
    low_res = RuleBasedRiskScorer.calculate_score([])
    assert low_res["risk_score"] == 0.0
    assert low_res["risk_category"] == "LOW"

    # Single moderate finding -> MEDIUM
    med_finding = [
        PatternFinding(
            pattern_id="PAT-FUND-CONSOLIDATION",
            pattern_name="Consolidation",
            severity="MEDIUM",
            confidence=0.8,
            description="Aggregated 3 deposits",
            wallet_address="0xwallet"
        ),
        PatternFinding(
            pattern_id="PAT-HIGH-FREQUENCY-BURST",
            pattern_name="Burst",
            severity="MEDIUM",
            confidence=0.8,
            description="Burst txs",
            wallet_address="0xwallet"
        )
    ]
    med_res = RuleBasedRiskScorer.calculate_score(med_finding, base_score=10.0)
    assert 25.0 <= med_res["risk_score"] <= 49.0
    assert med_res["risk_category"] == "MEDIUM"

def test_why_this_risk_explainability():
    low_res = RuleBasedRiskScorer.calculate_score([])
    why_low = RiskExplainability.generate_why_this_risk(low_res["contributions"], low_res["risk_category"])
    assert len(why_low) == 1
    assert "No anomalous" in why_low[0]

def test_ml_model_prediction_and_fallback():
    classifier = MLRiskClassifier(auto_init=True)
    features = {
        "transaction_count": 45.0,
        "unique_counterparties": 22.0,
        "incoming_value": 15.0,
        "outgoing_value": 14.8,
        "transaction_frequency": 3.0,
        "wallet_activity_duration": 5.0,
        "hop_count": 3.0,
        "fund_splitting_score": 0.8,
        "fund_concentration_score": 0.2,
        "high_risk_connections": 1.0,
        "cross_chain_indicator": 0.0,
        "rapid_movement_indicator": 1.0
    }

    pred = classifier.predict_risk(features)
    assert "model_available" in pred
    if pred["model_available"]:
        assert pred["model_name"] == "RandomForestClassifier"
        assert "feature_importance" in pred
        assert len(pred["feature_importance"]) > 0

    # Test fallback with empty / uninitialized classifier
    empty_classifier = MLRiskClassifier(auto_init=False)
    empty_classifier.model = None
    fallback_res = empty_classifier.predict_risk(features)
    assert fallback_res["model_available"] is False
    assert fallback_res["rule_based_risk_available"] is True
    assert "No validated model" in fallback_res["reason"]

def test_risk_api_endpoints():
    test_addr = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    res = client.get(f"/risk/wallet/{test_addr}")
    assert res.status_code == 200
    data = res.json()
    assert data["wallet_address"] == test_addr.lower()
    assert 0.0 <= data["risk_score"] <= 100.0
    assert data["risk_category"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert "contributions" in data
    assert "ml" in data

    # Case risk
    case_res = client.get("/risk/case/CASE-SIH2026-001")
    assert case_res.status_code == 200
    case_data = case_res.json()
    assert case_data["case_id"] == "CASE-SIH2026-001"
    assert 0.0 <= case_data["risk_score"] <= 100.0
