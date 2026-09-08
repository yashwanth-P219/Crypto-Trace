import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.database.models import Transaction, Case, AddressLabel, RiskAssessmentRecord
from app.risk.schemas import InvestigationRiskResponse, CaseRiskResponse, MLOutput, RiskFactorContribution
from app.risk.features import FeatureExtractor
from app.risk.rules import RuleBasedRiskScorer
from app.risk.model import MLRiskClassifier
from app.analysis.pattern_service import PatternService

class RiskService:
    _ml_classifier: Optional[MLRiskClassifier] = None

    @classmethod
    def get_ml_classifier(cls) -> MLRiskClassifier:
        if cls._ml_classifier is None:
            cls._ml_classifier = MLRiskClassifier(auto_init=True)
        return cls._ml_classifier

    @staticmethod
    def assess_wallet_risk(
        db: Session,
        wallet_address: str,
        case_id: Optional[str] = None,
        blockchain: str = "Ethereum",
        chain_id: int = 11155111,
        max_hops: int = 3,
        persist: bool = True
    ) -> InvestigationRiskResponse:
        norm_wallet = wallet_address.lower()

        # 1. Fetch transactions
        transactions = []
        if case_id:
            transactions = db.query(Transaction).filter(
                Transaction.case_id == case_id,
                (Transaction.from_address.ilike(norm_wallet)) |
                (Transaction.to_address.ilike(norm_wallet))
            ).all()

        if not transactions:
            transactions = db.query(Transaction).filter(
                (Transaction.from_address.ilike(norm_wallet)) |
                (Transaction.to_address.ilike(norm_wallet))
            ).all()

        # 2. Query Address Labels map
        labels_map = {lbl.address.lower(): lbl for lbl in db.query(AddressLabel).all()}

        # 3. Detect suspicious patterns via PatternService
        pattern_res = PatternService.analyze_wallet_patterns(
            db=db,
            wallet_address=norm_wallet,
            case_id=case_id,
            max_hops=max_hops,
            blockchain=blockchain,
            chain_id=chain_id,
            persist=persist
        )

        # 4. Extract explainable features
        features = FeatureExtractor.extract_wallet_features(
            wallet_address=norm_wallet,
            transactions=transactions,
            labels_map=labels_map,
            hop_count=max_hops,
            patterns_list=pattern_res.patterns
        )

        # 5. Deterministic rule-based scoring
        rule_res = RuleBasedRiskScorer.calculate_score(
            findings=pattern_res.patterns,
            features=features
        )

        # 6. Optional modular ML prediction
        ml_classifier = RiskService.get_ml_classifier()
        ml_res_dict = ml_classifier.predict_risk(features)
        ml_output = MLOutput(
            model_available=ml_res_dict.get("model_available", False),
            model_name=ml_res_dict.get("model_name"),
            model_version=ml_res_dict.get("model_version"),
            prediction=ml_res_dict.get("prediction"),
            ml_risk_probability=ml_res_dict.get("ml_risk_probability"),
            feature_importance=ml_res_dict.get("feature_importance", []),
            explanation=ml_res_dict.get("explanation", []),
            reason=ml_res_dict.get("reason"),
            rule_based_risk_available=True
        )

        risk_score = rule_res["risk_score"]
        risk_category = rule_res["risk_category"]

        # 7. Optionally persist assessment in risk_assessments table
        if persist:
            try:
                db.query(RiskAssessmentRecord).filter(
                    RiskAssessmentRecord.wallet_address.ilike(norm_wallet),
                    RiskAssessmentRecord.case_id == case_id
                ).delete(synchronize_session=False)

                rec = RiskAssessmentRecord(
                    case_id=case_id,
                    wallet_address=norm_wallet,
                    blockchain=blockchain,
                    chain_id=chain_id,
                    risk_score=risk_score,
                    risk_category=risk_category,
                    rule_based_score=rule_res["rule_based_score"],
                    ml_score=ml_output.ml_risk_probability,
                    model_name=ml_output.model_name if ml_output.model_available else None,
                    model_version=ml_output.model_version if ml_output.model_available else None,
                    contributions_json=[c.dict() for c in rule_res["contributions"]],
                    features_json=features,
                    created_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow()
                )
                db.add(rec)
                db.commit()
            except Exception:
                db.rollback()

        return InvestigationRiskResponse(
            wallet_address=norm_wallet,
            case_id=case_id,
            blockchain=blockchain,
            chain_id=chain_id,
            risk_score=risk_score,
            risk_category=risk_category,
            rule_based_score=rule_res["rule_based_score"],
            contributions=rule_res["contributions"],
            patterns_detected=rule_res["patterns_detected"],
            ml=ml_output,
            evidence=rule_res["evidence_txs"],
            assessed_at=datetime.datetime.utcnow()
        )

    @staticmethod
    def assess_case_risk(db: Session, case_id: str, max_hops: int = 3) -> CaseRiskResponse:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise ValueError(f"Case '{case_id}' not found.")

        wallet_assessment = RiskService.assess_wallet_risk(
            db=db,
            wallet_address=case.suspect_wallet,
            case_id=case_id,
            blockchain=case.blockchain or "Ethereum",
            max_hops=max_hops,
            persist=True
        )

        return CaseRiskResponse(
            case_id=case_id,
            suspect_wallet=case.suspect_wallet,
            blockchain=case.blockchain or "Ethereum",
            risk_score=wallet_assessment.risk_score,
            risk_category=wallet_assessment.risk_category,
            contributions=wallet_assessment.contributions,
            patterns_detected=wallet_assessment.patterns_detected,
            ml=wallet_assessment.ml,
            assessed_at=wallet_assessment.assessed_at
        )
