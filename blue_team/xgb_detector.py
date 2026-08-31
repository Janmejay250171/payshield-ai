import pandas as pd
import numpy as np

from xgboost import XGBClassifier

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    average_precision_score,
    confusion_matrix
)


class PayShieldXGB:

    def __init__(self):
        self.model = None

    def build_features(self, df):

        data = df.copy()

        data["timestamp"] = pd.to_datetime(data["timestamp"])

        data = data.sort_values(
            ["user_id", "timestamp"]
        ).reset_index(drop=True)

        # -----------------------------
        # TIME FEATURES
        # -----------------------------

        data["hour"] = data["timestamp"].dt.hour
        data["day_of_week"] = data["timestamp"].dt.dayofweek
        data["day"] = data["timestamp"].dt.day
        data["month"] = data["timestamp"].dt.month

        data["is_weekend"] = (
            data["day_of_week"] >= 5
        ).astype(int)

        data["is_night"] = (
            (data["hour"] < 6) |
            (data["hour"] >= 23)
        ).astype(int)

        # -----------------------------
        # USER TRANSACTION HISTORY
        # -----------------------------

        data["user_txn_count"] = (
            data.groupby("user_id")
            .cumcount()
        )

        data["previous_timestamp"] = (
            data.groupby("user_id")["timestamp"]
            .shift(1)
        )

        data["seconds_since_previous"] = (
            data["timestamp"]
            - data["previous_timestamp"]
        ).dt.total_seconds()

        data["seconds_since_previous"] = (
            data["seconds_since_previous"]
            .fillna(86400)
            .clip(lower=0)
        )

        # -----------------------------
        # VELOCITY SIGNALS
        # -----------------------------

        data["txn_within_1min"] = (
            data["seconds_since_previous"] <= 60
        ).astype(int)

        data["txn_within_5min"] = (
            data["seconds_since_previous"] <= 300
        ).astype(int)

        data["txn_within_10min"] = (
            data["seconds_since_previous"] <= 600
        ).astype(int)

        data["txn_within_1hour"] = (
            data["seconds_since_previous"] <= 3600
        ).astype(int)

        # -----------------------------
        # USER AMOUNT BEHAVIOR
        # -----------------------------

        user_mean = (
            data.groupby("user_id")["amount"]
            .transform("mean")
        )

        user_std = (
            data.groupby("user_id")["amount"]
            .transform("std")
        )

        user_median = (
            data.groupby("user_id")["amount"]
            .transform("median")
        )

        user_max = (
            data.groupby("user_id")["amount"]
            .transform("max")
        )

        user_min = (
            data.groupby("user_id")["amount"]
            .transform("min")
        )

        user_std = user_std.fillna(1)

        data["user_avg_amount"] = user_mean
        data["user_std_amount"] = user_std
        data["user_median_amount"] = user_median

        data["amount_deviation"] = (
            data["amount"] - user_mean
        )

        data["amount_zscore"] = (
            (data["amount"] - user_mean)
            / (user_std + 1)
        )

        data["amount_vs_median"] = (
            data["amount"]
            / (user_median + 1)
        )

        data["amount_vs_max"] = (
            data["amount"]
            / (user_max + 1)
        )

        data["amount_vs_min"] = (
            data["amount"]
            / (user_min + 1)
        )

        data["log_amount"] = np.log1p(
            data["amount"].clip(lower=0)
        )

        # -----------------------------
        # COUNTRY BEHAVIOR
        # -----------------------------

        common_country = (
            data.groupby("user_id")["country"]
            .transform(
                lambda x: x.mode().iloc[0]
                if not x.mode().empty
                else "unknown"
            )
        )

        data["country_changed"] = (
            data["country"] != common_country
        ).astype(int)

        # -----------------------------
        # DEVICE BEHAVIOR
        # -----------------------------

        common_device = (
            data.groupby("user_id")["device_type"]
            .transform(
                lambda x: x.mode().iloc[0]
                if not x.mode().empty
                else "unknown"
            )
        )

        data["device_changed"] = (
            data["device_type"] != common_device
        ).astype(int)

        data["unknown_device"] = (
            data["device_type"] == "unknown"
        ).astype(int)

        # -----------------------------
        # DOMAIN SIGNALS
        # -----------------------------

        suspicious_countries = [
            "RU",
            "NG",
            "CN"
        ]

        data["suspicious_country"] = (
            data["country"]
            .isin(suspicious_countries)
        ).astype(int)

        # -----------------------------
        # CATEGORICAL ENCODING
        # -----------------------------

        data = pd.get_dummies(
            data,
            columns=[
                "transaction_type",
                "country",
                "device_type"
            ],
            dtype=int
        )

        # Remove columns that must not enter model

        drop_columns = [
            "transaction_id",
            "user_id",
            "timestamp",
            "previous_timestamp",
            "is_fraud"
        ]

        features = data.drop(
            columns=[
                c for c in drop_columns
                if c in data.columns
            ],
            errors="ignore"
        )

        return features, data

    # --------------------------------------------------
    # TRAIN
    # --------------------------------------------------

    def train(self, df):

        X, processed = self.build_features(df)

        y = df["is_fraud"].reset_index(drop=True)

        X = X.reset_index(drop=True)

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.20,
            stratify=y,
            random_state=42
        )

        negative = (y_train == 0).sum()
        positive = (y_train == 1).sum()

        scale_pos_weight = negative / positive

        print()
        print("=" * 60)
        print("PAYSHIELD XGBOOST BEHAVIORAL MODEL")
        print("=" * 60)

        print(f"Training rows : {len(X_train)}")
        print(f"Testing rows  : {len(X_test)}")
        print(f"Fraud train   : {positive}")
        print(f"Normal train  : {negative}")
        print(
            f"Class weight  : "
            f"{scale_pos_weight:.2f}"
        )

        self.model = XGBClassifier(

            objective="binary:logistic",

            n_estimators=1000,

            learning_rate=0.03,

            max_depth=6,

            min_child_weight=3,

            subsample=0.85,

            colsample_bytree=0.85,

            gamma=0.1,

            reg_alpha=0.1,

            reg_lambda=2.0,

            scale_pos_weight=scale_pos_weight,

            eval_metric="aucpr",

            tree_method="hist",

            random_state=42,

            n_jobs=-1
        )

        print()
        print("Training XGBoost...")
        print("This may take a little while.")

        self.model.fit(
            X_train,
            y_train,
            eval_set=[
                (X_test, y_test)
            ],
            verbose=False
        )

        probabilities = (
            self.model
            .predict_proba(X_test)[:, 1]
        )

        predictions = (
            probabilities >= 0.50
        ).astype(int)

        print()
        print("=" * 60)
        print("MODEL RESULTS")
        print("=" * 60)

        print()

        print(
            classification_report(
                y_test,
                predictions,
                digits=4,
                zero_division=0
            )
        )

        roc_auc = roc_auc_score(
            y_test,
            probabilities
        )

        pr_auc = average_precision_score(
            y_test,
            probabilities
        )

        print(
            f"ROC-AUC : {roc_auc:.4f}"
        )

        print(
            f"PR-AUC  : {pr_auc:.4f}"
        )

        print()
        print("Confusion Matrix:")

        print(
            confusion_matrix(
                y_test,
                predictions
            )
        )

        print()
        print("=" * 60)

        return roc_auc, pr_auc


# ------------------------------------------------------
# MAIN
# ------------------------------------------------------

if __name__ == "__main__":

    print()
    print("Loading PayShield dataset...")

    df = pd.read_csv(
        "data/raw/transactions.csv"
    )

    print(
        f"Dataset shape: {df.shape}"
    )

    print(
        f"Fraud transactions: "
        f"{df['is_fraud'].sum()}"
    )

    print(
        f"Fraud rate: "
        f"{df['is_fraud'].mean() * 100:.2f}%"
    )

    detector = PayShieldXGB()

    detector.train(df)

    print()
    print("PayShield XGBoost experiment completed.")