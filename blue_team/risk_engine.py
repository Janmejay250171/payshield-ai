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

        self.xgb_model = None
        self.iso_model = None
        self.profiles = pd.DataFrame()
        self.meta = {
            "feature_columns": [],
            "global_avg_amt": 2500.0,
            "global_std_amt": 1000.0,
        }

        self.load_artifacts()
        self._seed_known_entities()

    def _seed_known_entities(self):
        """Seed initial nodes for graph visualization."""
        uids = []
        if isinstance(self.profiles, pd.DataFrame) and not self.profiles.empty and 'user_id' in self.profiles.columns:
            uids = self.profiles['user_id'].tolist()[:30]
        elif isinstance(self.profiles, dict):
            uids = list(self.profiles.keys())[:30]
            
        for uid in uids:
            self.graph_analyzer.add_transaction(
                txn_id=f"SEED_{uid}",
                user_id=uid,
                device_id=f"DEV_LEGIT_{uid[-4:]}",
                ip_address=f"192.168.1.{abs(hash(uid)) % 250 + 1}",
                recipient_id=None
            )

    def load_artifacts(self):
        """Load trained ML models and metadata."""
        xgb_path = os.path.join(self.models_dir, "xgb_model.pkl")
        iso_path = os.path.join(self.models_dir, "iso_model.pkl")
        prof_path = os.path.join(self.models_dir, "user_profiles.pkl")
        meta_path = os.path.join(self.models_dir, "pipeline_meta.pkl")

        try:
            if os.path.exists(xgb_path):
                self.xgb_model = joblib.load(xgb_path)

            if os.path.exists(iso_path):
                self.iso_model = joblib.load(iso_path)

            if os.path.exists(prof_path):
                self.profiles = pd.read_pickle(prof_path)

            if os.path.exists(meta_path):
                self.meta = joblib.load(meta_path)

            print("PayShield ML artifacts loaded successfully.")

        except Exception as exc:
            print(f"Warning: ML artifacts could not be loaded: {exc}")

    def _get_device_type(self, txn):
        device_type = txn.get("device_type")
        if device_type is None:
            return "unknown"
        device_type = str(device_type).strip().lower()
        if device_type in {"mobile", "tablet", "unknown"}:
            return device_type
        return "unknown"

    def _get_transaction_type(self, txn):
        transaction_type = txn.get("transaction_type", "UPI")
        transaction_type = str(transaction_type).strip().upper()
        allowed = {"NETBANKING", "UPI", "WALLET"}
        if transaction_type not in allowed:
            return "UPI"
        return transaction_type

    def _get_user_profile(self, user_id):
        if isinstance(self.profiles, pd.DataFrame):
            if self.profiles.empty or "user_id" not in self.profiles.columns:
                return (float(self.meta.get("global_avg_amt", 2500.0)), float(self.meta.get("global_std_amt", 1000.0)), "UNKNOWN", "UNKNOWN", 0)

            user_row = self.profiles[self.profiles["user_id"] == user_id]

            if user_row.empty:
                return (float(self.meta.get("global_avg_amt", 2500.0)), float(self.meta.get("global_std_amt", 1000.0)), "UNKNOWN", "UNKNOWN", 0)

            row = user_row.iloc[0]
            avg = float(row.get("user_avg_amount", self.meta.get("global_avg_amt", 2500.0)))
            std = float(row.get("user_std_amount", self.meta.get("global_std_amt", 1000.0)))
            common_country = row.get("common_country", "UNKNOWN")
            common_device = row.get("common_device", "UNKNOWN")
            txn_count = int(row.get("user_txn_count", 0))

            if std <= 0:
                std = float(self.meta.get("global_std_amt", 1000.0))

            return (avg, std, common_country, common_device, txn_count)
        else:
            profile = self.profiles.get(user_id, {"mean_amount": 2500.0, "std_amount": 1000.0})
            return (profile.get("mean_amount", 2500.0), profile.get("std_amount", 1000.0), "UNKNOWN", "UNKNOWN", 0)


    def _build_ml_features(self, txn):
        user_id = txn.get("user_id", "UNKNOWN")
        amount = float(txn.get("amount", 0.0))
        seconds_since_prev = float(txn.get("seconds_since_prev", 120.0))
        
        user_avg, user_std, common_country, common_device, user_txn_count = self._get_user_profile(user_id)

        timestamp = pd.to_datetime(txn.get("timestamp", pd.Timestamp.utcnow()), errors="coerce")
        if pd.isna(timestamp):
            timestamp = pd.Timestamp.utcnow()

        country = str(txn.get("country", "IN")).upper()
        device_type = self._get_device_type(txn)
        transaction_type = self._get_transaction_type(txn)

        velocity_1h = int(txn.get("velocity_1h", 0))

        if velocity_1h > 0 and seconds_since_prev == 120.0:
            seconds_since_prev = 3600.0 / velocity_1h

        velocity_10m = int(seconds_since_prev <= 600)
        country_changed = int(country != str(common_country).upper())
        device_changed = int(device_type != str(common_device).lower())

        row = {
            "amount": amount,
            "user_avg_amount": user_avg,
            "user_std_amount": user_std,
            "user_txn_count": float(user_txn_count),
            "log_amount": float(np.log1p(max(amount, 0))),
            "amount_to_avg_ratio": float(amount / (user_avg + 1e-5)),
            "amount_zscore": float((amount - user_avg) / (user_std + 1e-5)),
            "country_changed": country_changed,
            "device_changed": device_changed,
            "hour": float(timestamp.hour),
            "day_of_week": float(timestamp.dayofweek),
            "is_night": float(timestamp.hour >= 23 or timestamp.hour <= 5),
            "seconds_since_prev": float(seconds_since_prev),
            "velocity_10m": float(velocity_10m),
            "velocity_1h": float(velocity_1h),
            "transaction_type_NETBANKING": 0.0,
            "transaction_type_UPI": 0.0,
            "transaction_type_WALLET": 0.0,
            "country_GB": 0.0,
            "country_IN": 0.0,
            "country_NG": 0.0,
            "country_RU": 0.0,
            "country_SG": 0.0,
            "country_US": 0.0,
            "device_type_mobile": 0.0,
            "device_type_tablet": 0.0,
            "device_type_unknown": 0.0,
        }

        transaction_key = f"transaction_type_{transaction_type}"
        if transaction_key in row:
            row[transaction_key] = 1.0

        country_key = f"country_{country}"
        if country_key in row:
            row[country_key] = 1.0

        device_key = f"device_type_{device_type}"
        if device_key in row:
            row[device_key] = 1.0

        feature_columns = self.meta.get("feature_columns", [])
        
        if not feature_columns:
            return pd.DataFrame([row])

        return pd.DataFrame([row]).reindex(columns=feature_columns, fill_value=0.0).astype(float)

    def score_transaction(self, txn: dict) -> dict:
        user_id = txn.get("user_id", "UNKNOWN")
        device_id = txn.get("device_id", txn.get("device_type", "Dev_Default"))
        ip_address = txn.get("ip_address", "127.0.0.1")
        recipient_id = txn.get("recipient_id")
        transaction_id = txn.get("txn_id", txn.get("transaction_id", "TXN_LIVE"))

        self.graph_analyzer.add_transaction(transaction_id, user_id, device_id, ip_address, recipient_id)
        graph_score, graph_reasons = self.graph_analyzer.analyze_risk(user_id, device_id, ip_address, recipient_id)

        velocity_1h = int(txn.get("velocity_1h", 0))
        rule_txn = dict(txn)
        if velocity_1h > 0:
            rule_txn["seconds_since_prev"] = 3600.0 / velocity_1h
        elif "seconds_since_prev" not in rule_txn:
            rule_txn["seconds_since_prev"] = 86400.0

        user_avg, user_std, _, _, _ = self._get_user_profile(user_id)
        baseline = {"user_avg_amount": user_avg, "user_std_amount": user_std}
        rule_score, rule_reasons = self.rule_engine.evaluate(rule_txn, baseline)

        xgb_score = 0.05
        iso_score = 0.05
        ml_reasons = []

        if self.xgb_model is not None and self.iso_model is not None:
            try:
                features = self._build_ml_features(txn)
                
                xgb_score = float(self.xgb_model.predict_proba(features)[0, 1])
                if xgb_score > 0.65:
                    ml_reasons.append(f"ML_SUPERVISED: High statistical similarity to known fraud patterns ({xgb_score * 100:.1f}%)")

                iso_raw = float(-self.iso_model.decision_function(features)[0])
                iso_score = float(1.0 / (1.0 + np.exp(-iso_raw * 8)))
                
                if iso_score > 0.65:
                    ml_reasons.append(f"ANOMALY_DETECTOR: Unsupervised behavioral deviation detected ({iso_score * 100:.1f}%)")

            except Exception as exc:
                print(f"ML scoring warning: {exc}")

        composite_score = (xgb_score * 0.40) + (iso_score * 0.20) + (graph_score * 0.30) + (rule_score * 0.10)
        
        critical_signals = sum([xgb_score > 0.70, graph_score > 0.70, rule_score > 0.70, iso_score > 0.75])
        if critical_signals >= 2:
            composite_score = max(composite_score, 0.85)

        composite_score = float(np.clip(composite_score, 0.0, 1.0))

        if composite_score >= 0.70:
            decision = "BLOCK"
            risk_level = "CRITICAL"
        elif composite_score >= 0.40:
            decision = "REVIEW"
            risk_level = "ELEVATED"
        else:
            decision = "APPROVE"
            risk_level = "LOW"

        reasons = []
        reasons.extend(rule_reasons)
        reasons.extend(graph_reasons)
        reasons.extend(ml_reasons)

        if not reasons:
            reasons.append("Normal transactional behavior matching historical baseline")

        graph_data = self.graph_analyzer.get_subgraph(user_id)

        return {
            "transaction_id": transaction_id,
            "risk_score": round(composite_score, 4),
            "decision": decision,
            "risk_level": risk_level,
            "sub_scores": {
                "xgboost": round(xgb_score, 4),
                "isolation_forest": round(iso_score, 4),
                "graph_networkx": round(graph_score, 4),
                "rules": round(rule_score, 4),
            },
            "reasons": reasons,
            "graph": graph_data
        }