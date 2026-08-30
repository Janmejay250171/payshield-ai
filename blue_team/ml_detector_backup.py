import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score


class FraudDetector:

    def __init__(self):
        self.model = None
        self.user_profiles = None

    # ---------------------------------------------------------
    # BUILD HISTORICAL USER PROFILES
    # ---------------------------------------------------------

    def _build_profiles(self, df):

        data = df.copy()
        data["timestamp"] = pd.to_datetime(data["timestamp"])

        profiles = (
            data.groupby("user_id")
            .agg(
                user_avg_amount=("amount", "mean"),
                user_std_amount=("amount", "std"),
                user_transaction_count=("amount", "count"),
                common_country=("country", lambda x: x.mode()[0]),
                common_device=("device_type", lambda x: x.mode()[0]),
            )
            .reset_index()
        )

        profiles["user_std_amount"] = (
            profiles["user_std_amount"].fillna(1)
        )

        return profiles

    # ---------------------------------------------------------
    # FEATURE ENGINEERING
    # ---------------------------------------------------------

    def _features(self, df, profiles=None):

        data = df.copy()

        data["timestamp"] = pd.to_datetime(
            data["timestamp"]
        )

        data = data.sort_values(
            ["user_id", "timestamp"]
        )

        # Time features
        data["hour"] = data["timestamp"].dt.hour
        data["day_of_week"] = data["timestamp"].dt.dayofweek

        # Previous transaction
        data["previous_timestamp"] = (
            data.groupby("user_id")["timestamp"].shift(1)
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

        # Velocity
        data["velocity_10m"] = (
            data["seconds_since_previous"] <= 600
        ).astype(int)

        data["velocity_1h"] = (
            data["seconds_since_previous"] <= 3600
        ).astype(int)

        # Historical profiles
        if profiles is not None:

            data = data.merge(
                profiles,
                on="user_id",
                how="left"
            )

            data["user_avg_amount"] = (
                data["user_avg_amount"]
                .fillna(data["amount"].median())
            )

            data["user_std_amount"] = (
                data["user_std_amount"]
                .fillna(data["amount"].std())
            )

            data["amount_zscore"] = (
                data["amount"]
                - data["user_avg_amount"]
            ) / (
                data["user_std_amount"] + 1
            )

            data["country_changed"] = (
                data["country"]
                != data["common_country"]
            ).astype(int)

            data["device_changed"] = (
                data["device_type"]
                != data["common_device"]
            ).astype(int)

        else:

            data["user_avg_amount"] = data["amount"].median()
            data["user_std_amount"] = data["amount"].std()
            data["amount_zscore"] = 0
            data["country_changed"] = 0
            data["device_changed"] = 0

        # Domain signals
        data["suspicious_country"] = (
            data["country"]
            .isin(["RU", "NG", "CN"])
        ).astype(int)

        data["unknown_device"] = (
            data["device_type"] == "unknown"
        ).astype(int)

        data["night_transaction"] = (
            (data["hour"] <= 5)
            | (data["hour"] >= 23)
        ).astype(int)

        data["log_amount"] = np.log1p(
            data["amount"].clip(lower=0)
        )

        features = [
            "amount",
            "log_amount",
            "user_avg_amount",
            "user_std_amount",
            "amount_zscore",
            "seconds_since_previous",
            "velocity_10m",
            "velocity_1h",
            "country_changed",
            "device_changed",
            "suspicious_country",
            "unknown_device",
            "night_transaction",
            "hour",
            "day_of_week",
            "transaction_type",
            "country",
            "device_type",
        ]

        return data[features]

    # ---------------------------------------------------------
    # TRAIN
    # ---------------------------------------------------------

    def train(self, df):

        # Split FIRST
        train_df, test_df = train_test_split(
            df,
            test_size=0.20,
            stratify=df["is_fraud"],
            random_state=42
        )

        # Profiles are created ONLY from training data
        self.user_profiles = self._build_profiles(
            train_df
        )

        X_train = self._features(
            train_df,
            self.user_profiles
        )

        X_test = self._features(
            test_df,
            self.user_profiles
        )

       y_train = train_df["is_fraud"].loc[X_train.index]

        y_test = test_df.loc[
            X_test.index,
            "is_fraud"
        ]

        categorical = [
            "transaction_type",
            "country",
            "device_type",
        ]

        numerical = [
            c for c in X_train.columns
            if c not in categorical
        ]

        preprocessor = ColumnTransformer(
            [
                (
                    "num",
                    "passthrough",
                    numerical
                ),
                (
                    "cat",
                    OneHotEncoder(
                        handle_unknown="ignore"
                    ),
                    categorical
                ),
            ]
        )

        self.model = Pipeline(
            [
                (
                    "preprocessor",
                    preprocessor
                ),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=500,
                        max_depth=14,
                        min_samples_leaf=2,
                        class_weight="balanced",
                        random_state=42,
                        n_jobs=-1
                    )
                )
            ]
        )

        self.model.fit(
            X_train,
            y_train
        )

        predictions = self.model.predict(
            X_test
        )

        probabilities = (
            self.model.predict_proba(X_test)[:, 1]
        )

        print("\n=== PayShield Blue Team ML ===")

        print(
            classification_report(
                y_test,
                predictions,
                digits=4,
                zero_division=0
            )
        )

        print(
            f"ROC-AUC: "
            f"{roc_auc_score(y_test, probabilities):.4f}"
        )

    # ---------------------------------------------------------
    # PREDICTION API
    # ---------------------------------------------------------

    def predict(self, transactions):

        if self.model is None:
            raise RuntimeError(
                "Model has not been trained."
            )

        X = self._features(
            transactions,
            self.user_profiles
        )

        probabilities = (
            self.model.predict_proba(X)[:, 1]
        )

        results = transactions.copy()

        results["fraud_probability"] = (
            probabilities.round(4)
        )

        results["risk_score"] = (
            probabilities * 100
        ).round(2)

        results["is_suspicious"] = (
            probabilities >= 0.5
        )

        return results


# -------------------------------------------------------------
# TEST
# -------------------------------------------------------------

if __name__ == "__main__":

    df = pd.read_csv(
        "data/raw/transactions.csv"
    )

    detector = FraudDetector()

    detector.train(df)

    results = detector.predict(df)

    print("\nHighest-risk transactions:")

    print(
        results[
            [
                "transaction_id",
                "user_id",
                "amount",
                "fraud_probability",
                "risk_score",
                "is_suspicious"
            ]
        ]
        .sort_values(
            "fraud_probability",
            ascending=False
        )
        .head(10)
        .to_string(index=False)
    )