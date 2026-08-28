import pandas as pd


class BlueTeamDetector:
    def __init__(self, amount_threshold=1000):
        self.amount_threshold = amount_threshold

    def detect(self, transactions):
        df = transactions.copy()

        df["risk_score"] = 0

        df.loc[df["amount"] > self.amount_threshold, "risk_score"] += 40
        df.loc[df["country"].isin(["RU", "NG", "CN"]), "risk_score"] += 30
        df.loc[df["device_type"] == "unknown", "risk_score"] += 30

        df["is_suspicious"] = df["risk_score"] >= 50

        return df


if __name__ == "__main__":
    df = pd.read_csv("data/raw/transactions.csv")

    detector = BlueTeamDetector()

    results = detector.detect(df)

    print("Blue Team detection completed.")
    print(results[results["is_suspicious"]].head())

    print(f"\nSuspicious transactions: {results['is_suspicious'].sum()}")