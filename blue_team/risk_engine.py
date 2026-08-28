import os
import joblib
import pandas as pd
import numpy as np
from blue_team.rule_engine import RuleEngine
from blue_team.graph_analyzer import GraphAnalyzer

class PayShieldRiskEngine:
    def __init__(self, artifacts_dir="models_saved"):
        self.rule_engine = RuleEngine()
        self.graph_analyzer = GraphAnalyzer()
        self.artifacts_dir = artifacts_dir
        self.load_artifacts()

    def load_artifacts(self):
        xgb_path = os.path.join(self.artifacts_dir, "xgb_model.pkl")
        iso_path = os.path.join(self.artifacts_dir, "iso_model.pkl")
        prof_path = os.path.join(self.artifacts_dir, "user_profiles.pkl")
        meta_path = os.path.join(self.artifacts_dir, "pipeline_meta.pkl")

        if os.path.exists(xgb_path) and os.path.exists(iso_path):
            self.xgb_model = joblib.load(xgb_path)
            self.iso_model = joblib.load(iso_path)
            self.profiles = pd.read_pickle(prof_path)
            self.meta = joblib.load(meta_path)
        else:
            self.xgb_model = None
            self.iso_model = None
            self.profiles = pd.DataFrame()
            self.meta = {"feature_columns": [], "global_avg_amt": 2500.0, "global_std_amt": 1000.0}

    def score_transaction(self, txn: dict) -> dict:
        user_id = txn.get("user_id", "UNKNOWN")
        device_id = txn.get("device_type", "UNKNOWN_DEV")
        ip_address = txn.get("ip_address", "127.0.0.1")
        recipient_id = txn.get("recipient_id", None)
        amount = float(txn.get("amount", 0.0))

        # Retrieve user profile
        user_row = self.profiles[self.profiles['user_id'] == user_id] if not self.profiles.empty else pd.DataFrame()
        if not user_row.empty:
            u_avg = float(user_row['user_avg_amount'].iloc[0])
            u_std = float(user_row['user_std_amount'].iloc[0])
            c_country = user_row['common_country'].iloc[0]
            c_device = user_row['common_device'].iloc[0]
        else:
            u_avg = self.meta.get("global_avg_amt", 2500.0)
            u_std = self.meta.get("global_std_amt", 1000.0)
            c_country = "UNKNOWN"
            c_device = "UNKNOWN"

        baseline_dict = {"user_avg_amount": u_avg, "user_std_amount": u_std}

        # 1. Rules Sub-Score
        rule_score, rule_reasons = self.rule_engine.evaluate(txn, baseline_dict)

        # 2. Graph Sub-Score (NetworkX)
        self.graph_analyzer.add_transaction(txn.get("transaction_id", "T0"), user_id, device_id, ip_address, recipient_id)
        graph_score, graph_reasons = self.graph_analyzer.analyze_risk(user_id, device_id, ip_address, recipient_id)

        # 3. Supervised (XGBoost) & Anomaly (Isolation Forest)
        txn_time = pd.to_datetime(txn.get("timestamp", pd.Timestamp.utcnow()))
        hour = txn_time.hour
        is_night = 1 if (hour >= 23 or hour <= 5) else 0
        seconds_prev = float(txn.get("seconds_since_prev", 86400.0))

        amt_ratio = amount / (u_avg + 1e-5)
        amt_zscore = (amount - u_avg) / (u_std + 1e-5)
        country_changed = int(txn.get("country") != c_country)
        device_changed = int(device_id != c_device)

        row_dict = {
            "amount": amount,
            "user_avg_amount": u_avg,
            "user_std_amount": u_std,
            "user_txn_count": 1.0,
            "log_amount": float(np.log1p(amount)),
            "amount_to_avg_ratio": float(amt_ratio),
            "amount_zscore": float(amt_zscore),
            "country_changed": country_changed,
            "device_changed": device_changed,
            "hour": float(hour),
            "day_of_week": float(txn_time.dayofweek),
            "is_night": float(is_night),
            "seconds_since_prev": seconds_prev,
            "velocity_10m": float(int(seconds_prev <= 600)),
            "velocity_1h": float(int(seconds_prev <= 3600)),
            f"transaction_type_{txn.get('transaction_type', 'PAYMENT')}": 1.0,
            f"country_{txn.get('country', 'IN')}": 1.0,
            f"device_type_{device_id}": 1.0
        }

        feature_cols = self.meta.get("feature_columns", [])
        if self.xgb_model and feature_cols:
            input_vector = pd.DataFrame([row_dict]).reindex(columns=feature_cols, fill_value=0.0).astype(float)
            xgb_score = float(self.xgb_model.predict_proba(input_vector)[0, 1])
            iso_raw = float(-self.iso_model.decision_function(input_vector)[0])
            iso_score = float(1.0 / (1.0 + np.exp(-iso_raw * 8)))
        else:
            xgb_score = 0.05
            iso_score = 0.05

        # 4. Blueprint Weighted Formula (Section 10)
        composite_score = (xgb_score * 0.4) + (iso_score * 0.2) + (graph_score * 0.3) + (rule_score * 0.1)

        # High-confidence escalation if multiple critical layers trigger
        critical_signals = (xgb_score > 0.70) + (graph_score > 0.70) + (rule_score > 0.70) + (iso_score > 0.75)
        if critical_signals >= 2:
            composite_score = max(composite_score, 0.85)

        composite_score = float(np.clip(composite_score, 0.0, 1.0))

        # 5. Master Decision Thresholds (Blueprint Section 10)
        if composite_score >= 0.75:
            decision = "BLOCK"
            risk_level = "CRITICAL"
        elif composite_score >= 0.45:
            decision = "REVIEW"
            risk_level = "HIGH"
        elif composite_score >= 0.25:
            decision = "REVIEW"
            risk_level = "MEDIUM"
        else:
            decision = "APPROVE"
            risk_level = "LOW"

        all_reasons = []
        all_reasons.extend(rule_reasons)
        all_reasons.extend(graph_reasons)
        if xgb_score > 0.65:
            all_reasons.append(f"ML_SUPERVISED: High statistical similarity to known fraud patterns ({xgb_score*100:.1f}%)")
        if iso_score > 0.70:
            all_reasons.append(f"ML_ANOMALY: Significant zero-day deviation from normal baseline ({iso_score*100:.1f}%)")
        if not all_reasons:
            all_reasons.append("Normal transactional behavior matching historical baseline")

        return {
            "transaction_id": txn.get("transaction_id", "TXN_SIM"),
            "risk_score": round(composite_score, 4),
            "decision": decision,
            "risk_level": risk_level,
            "sub_scores": {
                "xgboost": round(xgb_score, 4),
                "isolation_forest": round(iso_score, 4),
                "graph_networkx": round(graph_score, 4),
                "rules": round(rule_score, 4)
            },
            "reasons": all_reasons
        }