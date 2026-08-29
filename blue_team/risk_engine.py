import os
import joblib
import numpy as np
import pandas as pd
from blue_team.rule_engine import RuleEngine
from blue_team.graph_analyzer import GraphAnalyzer

class PayShieldRiskEngine:
    def __init__(self, models_dir: str = "models_saved"):
        self.models_dir = models_dir
        self.rule_engine = RuleEngine()
        self.graph_analyzer = GraphAnalyzer()

        self.xgb_model = joblib.load(os.path.join(models_dir, "xgb_model.pkl"))
        self.iso_model = joblib.load(os.path.join(models_dir, "iso_model.pkl"))
        self.user_profiles = joblib.load(os.path.join(models_dir, "user_profiles.pkl"))
        self.pipeline_meta = joblib.load(os.path.join(models_dir, "pipeline_meta.pkl"))
        self.feature_cols = self.pipeline_meta["feature_cols"]

        self._seed_known_entities()

    def _seed_known_entities(self):
        for uid in list(self.user_profiles.keys())[:30]:
            self.graph_analyzer.add_transaction(
                txn_id=f"SEED_{uid}",
                user_id=uid,
                device_id=f"DEV_LEGIT_{uid[-4:]}",
                ip_address=f"192.168.1.{abs(hash(uid)) % 250 + 1}"
            )

    def extract_features(self, txn: dict) -> pd.DataFrame:
        user_id = txn.get("user_id", "USER_UNKNOWN")
        amount = float(txn.get("amount", 0.0))
        seconds_prev = float(txn.get("seconds_since_prev", 120.0))
        txn_type = str(txn.get("transaction_type", "PAYMENT")).upper()

        profile = self.user_profiles.get(user_id, {"mean_amount": 500.0, "std_amount": 100.0})
        mean_amt = profile["mean_amount"]
        std_amt = profile["std_amount"] if profile["std_amount"] > 0 else 1.0

        z_score = (amount - mean_amt) / std_amt
        amount_ratio = amount / max(mean_amt, 1.0)
        is_type_transfer = 1 if txn_type == "TRANSFER" else 0

        row = {
            "amount": amount,
            "seconds_since_prev": seconds_prev,
            "z_score": z_score,
            "amount_ratio": amount_ratio,
            "is_type_transfer": is_type_transfer
        }
        return pd.DataFrame([row])[self.feature_cols]

    def score_transaction(self, txn: dict) -> dict:
        user_id = txn.get("user_id", "USER_UNKNOWN")
        device_id = txn.get("device_type", "Dev_Default")
        ip_addr = txn.get("ip_address", "127.0.0.1")
        recipient_id = txn.get("recipient_id", None)

        self.graph_analyzer.add_transaction(
            txn_id=txn.get("transaction_id", "TXN_LIVE"),
            user_id=user_id,
            device_id=device_id,
            ip_address=ip_addr,
            recipient_id=recipient_id
        )

        all_reasons = []

        # Layer 1: Rule Engine
        rule_score, rule_reasons = self.rule_engine.evaluate(txn, self.user_profiles)
        all_reasons.extend(rule_reasons)

        # Layer 2 & 3: XGBoost and Isolation Forest
        X = self.extract_features(txn)
        xgb_score = float(self.xgb_model.predict_proba(X)[0][1])
        if xgb_score > 0.70:
            all_reasons.append(f"ML_SUPERVISED: High statistical similarity to known fraud patterns ({xgb_score*100:.1f}%)")

        iso_raw = float(-self.iso_model.score_samples(X)[0])
        iso_score = float(1.0 / (1.0 + np.exp(-10.0 * (iso_raw - 0.55))))
        if iso_score > 0.65:
            all_reasons.append(f"ANOMALY_DETECTOR: Unsupervised zero-day behavioral deviation detected ({iso_score*100:.1f}%)")

        # Layer 4: NetworkX Graph
        graph_score, graph_reasons = self.graph_analyzer.analyze_risk(user_id, device_id, ip_addr, recipient_id)
        all_reasons.extend(graph_reasons)

        composite_score = (
            xgb_score * 0.40 +
            iso_score * 0.20 +
            graph_score * 0.30 +
            rule_score * 0.10
        )
        composite_score = min(max(composite_score, 0.0), 1.0)

        if composite_score >= 0.70:
            decision = "BLOCK"
            risk_level = "CRITICAL"
        elif composite_score >= 0.40:
            decision = "REVIEW"
            risk_level = "ELEVATED"
        else:
            decision = "APPROVE"
            risk_level = "LOW"

        graph_data = self.graph_analyzer.get_subgraph(user_id)

        return {
            "transaction_id": txn.get("transaction_id", "TXN_LIVE"),
            "risk_score": round(composite_score, 4),
            "decision": decision,
            "risk_level": risk_level,
            "sub_scores": {
                "xgboost": round(xgb_score, 4),
                "isolation_forest": round(iso_score, 4),
                "graph_networkx": round(graph_score, 4),
                "rules": round(rule_score, 4)
            },
            "reasons": all_reasons,
            "graph": graph_data
        }