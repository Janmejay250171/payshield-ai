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

    # =========================================================
    # BUILD HISTORICAL USER PROFILES
    # =========================================================

    def _build_profiles(self, df):

        data = df.copy()

        data["timestamp"] = pd.to_datetime(
            data["timestamp"],
            errors="coerce"
        )

        profiles = (
            data.groupby("user_id")
            .agg(
                user_avg_amount=("amount", "mean"),
                user_std_amount=("amount", "std"),
                user_transaction_count=("amount", "count"),
                common_country=(
                    "country",
                    lambda x: x.mode().iloc[0]
                    if not x.mode().empty
                    else "unknown"
                ),
                common_device=(
                    "device_type",
                    lambda x: x.mode().iloc[0]
                    if not x.mode().empty
                    else "unknown"
                ),
            )
            .reset_index()
        )

        profiles["user_std_amount"] = (
            profiles["user_std_amount"]
            .fillna(0)
        )

        return profiles

    # =========================================================
    # FEATURE ENGINEERING
    # =========================================================

    def _features(self, df, profiles=None):

        data = df.copy()

        # Preserve original row identity
        data["_original_index"] = data.index

        data["timestamp"] = pd.to_datetime(
            data["timestamp"],
            errors="coerce"
        )

        # Sort for temporal feature calculation
        data = data.sort_values(
            ["user_id", "timestamp"]
        )

        # -----------------------------------------------------
        # TIME FEATURES
        # -----------------------------------------------------

        data["hour"] = data["timestamp"].dt.hour.fillna(12)

        data["day_of_week"] = (
            data["timestamp"]
            .dt.dayofweek
            .fillna(0)
        )

        # -----------------------------------------------------
        # PREVIOUS TRANSACTION
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # VELOCITY
        # -----------------------------------------------------

        data["velocity_10m"] = (
            data["seconds_since_previous"] <= 600
        ).astype(int)

        data["velocity_1h"] = (
            data["seconds_since_previous"] <= 3600
        ).astype(int)

        # -----------------------------------------------------
        # USER HISTORICAL PROFILE
        # -----------------------------------------------------

        if profiles is not None:

            data = data.merge(
                profiles,
                on="user_id",
                how="left"
            )

            # Fill missing profile values
            data["user_avg_amount"] = (
                data["user_avg_amount"]
                .fillna(data["amount"].median())
            )

            data["user_std_amount"] = (
                data["user_std_amount"]
                .fillna(data["amount"].std())
            )

            data["user_std_amount"] = (
                data["user_std_amount"]
                .replace(0, 1)
            )

            # -------------------------------------------------
            # AMOUNT ANOMALY
            # -------------------------------------------------

            data["amount_zscore"] = (
                data["amount"]
                - data["user_avg_amount"]
            ) / (
                data["user_std_amount"] + 1
            )

            # -------------------------------------------------
            # COUNTRY CHANGE
            # -------------------------------------------------

            data["country_changed"] = (
                data["country"]
                != data["common_country"]
            ).astype(int)

            # -------------------------------------------------
            # DEVICE CHANGE
            # -------------------------------------------------

            data["device_changed"] = (
                data["device_type"]
                != data["common_device"]
            ).astype(int)

        else:

            median_amount = data["amount"].median()
            std_amount = data["amount"].std()

            if pd.isna(std_amount) or std_amount == 0:
                std_amount = 1

            data["user_avg_amount"] = median_amount
            data["user_std_amount"] = std_amount
            data["amount_zscore"] = 0
            data["country_changed"] = 0
            data["device_changed"] = 0

        # -----------------------------------------------------
        # DOMAIN SIGNALS
        # -----------------------------------------------------

        suspicious_countries = [
            "RU",
            "NG",
            "CN"
        ]

        data["suspicious_country"] = (
            data["country"]
            .isin(suspicious_countries)
        ).astype(int)

        data["unknown_device"] = (
            data["device_type"]
            .astype(str)
            .str.lower()
            == "unknown"
        ).astype(int)

        data["night_transaction"] = (
            (data["hour"] <= 5)
            | (data["hour"] >= 23)
        ).astype(int)

        # -----------------------------------------------------
        # LOG AMOUNT
        # -----------------------------------------------------

        data["log_amount"] = np.log1p(
            data["amount"]
            .clip(lower=0)
        )

        # -----------------------------------------------------
        # FEATURE LIST
        # -----------------------------------------------------

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

        result = data[features].copy()

        # -----------------------------------------------------
        # CRITICAL:
        # Restore original dataframe index.
        #
        # This prevents the KeyError you were getting because
        # _features() sorts the dataframe by user/time.
        # -----------------------------------------------------

        result.index = data["_original_index"].values

        # Ensure unique index
        result = result.sort_index()

        return result

    # =========================================================
    # TRAIN
    # =========================================================

    def train(self, df):

        print("\nPreparing PayShield ML model...")

        # -----------------------------------------------------
        # Reset index BEFORE splitting
        # -----------------------------------------------------

        df = df.copy().reset_index(drop=True)

        # -----------------------------------------------------
        # TRAIN / TEST SPLIT
        # -----------------------------------------------------

        train_df, test_df = train_test_split(
            df,
            test_size=0.20,
            stratify=df["is_fraud"],
            random_state=42
        )

        # Reset indexes independently
        train_df = train_df.reset_index(drop=True)
        test_df = test_df.reset_index(drop=True)

        # -----------------------------------------------------
        # BUILD PROFILES ONLY FROM TRAINING DATA
        # -----------------------------------------------------

        self.user_profiles = self._build_profiles(
            train_df
        )

        # -----------------------------------------------------
        # CREATE FEATURES
        # -----------------------------------------------------

        X_train = self._features(
            train_df,
            self.user_profiles
        )

        X_test = self._features(
            test_df,
            self.user_profiles
        )

        # -----------------------------------------------------
        # CRITICAL FIX:
        #
        # _features() restores the original dataframe index,
        # so labels can safely be aligned using reindex().
        # -----------------------------------------------------

        y_train = (
            train_df["is_fraud"]
            .reindex(X_train.index)
        )

        y_test = (
            test_df["is_fraud"]
            .reindex(X_test.index)
        )

        # Safety check
        if y_train.isna().any():
            raise ValueError(
                "Training label alignment failed."
            )

        if y_test.isna().any():
            raise ValueError(
                "Test label alignment failed."
            )

        # -----------------------------------------------------
        # CATEGORICAL FEATURES
        # -----------------------------------------------------

        categorical = [
            "transaction_type",
            "country",
            "device_type",
        ]

        # -----------------------------------------------------
        # NUMERICAL FEATURES
        # -----------------------------------------------------

        numerical = [
            column
            for column in X_train.columns
            if column not in categorical
        ]

        # -----------------------------------------------------
        # PREPROCESSOR
        # -----------------------------------------------------

        preprocessor = ColumnTransformer(
            transformers=[
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
                )
            ]
        )

        # -----------------------------------------------------
        # RANDOM FOREST
        # -----------------------------------------------------

        classifier = RandomForestClassifier(
            n_estimators=500,
            max_depth=14,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )

        # -----------------------------------------------------
        # COMPLETE PIPELINE
        # -----------------------------------------------------

        self.model = Pipeline(
            steps=[
                (
                    "preprocessor",
                    preprocessor
                ),
                (
                    "classifier",
                    classifier
                )
            ]
        )

        # -----------------------------------------------------
        # TRAIN
        # -----------------------------------------------------

        print("Training Random Forest...")

        self.model.fit(
            X_train,
            y_train
        )

        # -----------------------------------------------------
        # PREDICTIONS
        # -----------------------------------------------------

        predictions = self.model.predict(
            X_test
        )

        probabilities = (
            self.model
            .predict_proba(X_test)[:, 1]
        )

        # -----------------------------------------------------
        # RESULTS
        # -----------------------------------------------------

        print("\n" + "=" * 60)
        print("=== PayShield Blue Team ML ===")
        print("=" * 60)

        print(
            classification_report(
                y_test,
                predictions,
                digits=4,
                zero_division=0
            )
        )

        auc = roc_auc_score(
            y_test,
            probabilities
        )

        print(
            f"ROC-AUC: {auc:.4f}"
        )

        print("=" * 60)

    # =========================================================
    # PREDICTION API
    # =========================================================

    def predict(self, transactions):

        if self.model is None:
            raise RuntimeError(
                "Model has not been trained."
            )

        transactions = transactions.copy()

        X = self._features(
            transactions,
            self.user_profiles
        )

        probabilities = (
            self.model
            .predict_proba(X)[:, 1]
        )

        # -----------------------------------------------------
        # Restore transaction ordering
        # -----------------------------------------------------

        results = transactions.copy()

        # X has original indexes
        results = results.loc[X.index].copy()

        results["fraud_probability"] = (
            probabilities.round(4)
        )

        results["risk_score"] = (
            probabilities * 100
        ).round(2)

        results["is_suspicious"] = (
            probabilities >= 0.50
        )

        return results

    # =========================================================
    # SAVE MODEL
    # =========================================================

    def save(self, path="blue_team/payshield_model.pkl"):

        import joblib

        joblib.dump(
            self,
            path
        )

        print(
            f"\nModel saved to: {path}"
        )

    # =========================================================
    # LOAD MODEL
    # =========================================================

    @staticmethod
    def load(path="blue_team/payshield_model.pkl"):

        import joblib

        detector = joblib.load(path)

        return detector


# =============================================================
# MAIN TEST
# =============================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("PAYSHIELD BEHAVIORAL ML")
    print("=" * 60)

    # ---------------------------------------------------------
    # LOAD DATASET
    # ---------------------------------------------------------

    df = pd.read_csv(
        "data/raw/transactions.csv"
    )

    print(
        f"\nDataset shape: {df.shape}"
    )

    print(
        f"Fraud transactions: "
        f"{df['is_fraud'].sum()}"
    )

    print(
        f"Fraud rate: "
        f"{df['is_fraud'].mean():.2%}"
    )

    # ---------------------------------------------------------
    # CREATE DETECTOR
    # ---------------------------------------------------------

    detector = FraudDetector()

    # ---------------------------------------------------------
    # TRAIN
    # ---------------------------------------------------------

    detector.train(df)

    # ---------------------------------------------------------
    # PREDICT
    # ---------------------------------------------------------

    results = detector.predict(
        df
    )

    # ---------------------------------------------------------
    # TOP 10 HIGHEST RISK
    # ---------------------------------------------------------

    print("\nHighest-risk transactions:")

    top_risk = (
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
    )

    print(
        top_risk.to_string(
            index=False
        )
    )

    print("\nPayShield ML completed successfully.")