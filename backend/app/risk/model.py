import os
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = Path(__file__).resolve().parent.parent.parent.parent / "ml" / "models" / "risk_rf_model.joblib"

class MLRiskClassifier:
    """
    Modular Machine Learning risk prediction layer using scikit-learn.
    Does NOT replace transparent rule-based scoring.
    Trained on synthetic demonstration topologies without unverified real-world accuracy claims.
    """
    FEATURE_NAMES = [
        "transaction_count",
        "unique_counterparties",
        "incoming_value",
        "outgoing_value",
        "transaction_frequency",
        "wallet_activity_duration",
        "hop_count",
        "fund_splitting_score",
        "fund_concentration_score",
        "high_risk_connections",
        "cross_chain_indicator",
        "rapid_movement_indicator"
    ]

    MODEL_NAME = "RandomForestClassifier"
    MODEL_VERSION = "1.0.0-demo"

    def __init__(self, auto_init: bool = True):
        self.model: Optional[RandomForestClassifier] = None
        if auto_init:
            self._load_or_train_baseline()

    def _load_or_train_baseline(self):
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        if MODEL_PATH.exists():
            try:
                self.model = joblib.load(MODEL_PATH)
                return
            except Exception:
                pass

        try:
            # Train transparent synthetic demonstration baseline model
            np.random.seed(42)
            n_samples = 400

            # Normal wallet distribution
            normal_feats = np.random.normal(
                loc=[10, 8, 1.0, 0.8, 0.1, 100.0, 1.0, 0.1, 0.1, 0.0, 0.0, 0.0],
                scale=[5, 3, 0.5, 0.4, 0.05, 50.0, 0.5, 0.05, 0.05, 0.0, 0.0, 0.0],
                size=(n_samples // 2, len(self.FEATURE_NAMES))
            )
            normal_feats = np.clip(normal_feats, 0, None)
            normal_labels = np.zeros(n_samples // 2)

            # Layering/mule wallet distribution
            suspicious_feats = np.random.normal(
                loc=[40, 25, 15.0, 14.8, 2.5, 5.0, 3.5, 0.8, 0.2, 1.5, 0.5, 0.9],
                scale=[10, 8, 5.0, 5.0, 1.0, 2.0, 1.0, 0.2, 0.1, 0.5, 0.5, 0.1],
                size=(n_samples // 2, len(self.FEATURE_NAMES))
            )
            suspicious_feats = np.clip(suspicious_feats, 0, None)
            suspicious_labels = np.ones(n_samples // 2)

            X = np.vstack([normal_feats, suspicious_feats])
            y = np.concatenate([normal_labels, suspicious_labels])

            rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
            rf.fit(X, y)
            self.model = rf
            joblib.dump(rf, MODEL_PATH)
        except Exception:
            self.model = None

    def is_available(self) -> bool:
        return self.model is not None

    def predict_risk(self, feature_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Runs RF inference and extracts top contributing features.
        Gracefully handles missing model without throwing exceptions.
        """
        if not self.model:
            return {
                "model_available": False,
                "model_name": self.MODEL_NAME,
                "model_version": self.MODEL_VERSION,
                "reason": "No validated model is configured.",
                "rule_based_risk_available": True
            }

        try:
            vector = [float(feature_dict.get(feat, 0.0)) for feat in self.FEATURE_NAMES]
            probs = self.model.predict_proba([vector])[0]
            suspicious_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])

            importances = self.model.feature_importances_
            feature_contributions = []
            for name, val, imp in zip(self.FEATURE_NAMES, vector, importances):
                feature_contributions.append({
                    "feature": name,
                    "value": round(float(val), 4),
                    "model_importance": round(float(imp), 4)
                })

            feature_contributions.sort(key=lambda x: x["model_importance"], reverse=True)

            prediction_label = "ELEVATED_ANALYTIC_RISK" if suspicious_prob >= 0.5 else "BASELINE_PROFILE"

            explanations = [
                f"Top contributing feature: {f['feature']} (value: {f['value']}, weight: {f['model_importance']})"
                for f in feature_contributions[:3]
            ]

            return {
                "model_available": True,
                "model_name": self.MODEL_NAME,
                "model_version": self.MODEL_VERSION,
                "prediction": prediction_label,
                "ml_risk_probability": round(suspicious_prob, 4),
                "suggested_score_contribution": round(suspicious_prob * 25.0, 1),
                "feature_importance": feature_contributions[:5],
                "explanation": explanations,
                "rule_based_risk_available": True
            }
        except Exception as e:
            return {
                "model_available": False,
                "model_name": self.MODEL_NAME,
                "model_version": self.MODEL_VERSION,
                "reason": f"Inference error: {str(e)}",
                "rule_based_risk_available": True
            }
