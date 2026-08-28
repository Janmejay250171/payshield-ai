import pandas as pd
import numpy as np


class RedTeam:

    def __init__(self, random_state=42):
        self.rng = np.random.default_rng(random_state)

    def high_value_attack(self, df, fraction=0.25):
        attacked = df.copy()

        fraud_idx = attacked.index[attacked["is_fraud"] == 1]
        count = max(1, int(len(fraud_idx) * fraction))
        selected = self.rng.choice(fraud_idx, count, replace=False)

        attacked.loc[selected, "amount"] *= self.rng.uniform(
            5, 20, size=count
        )

        return attacked

    def device_change_attack(self, df, fraction=0.25):
        attacked = df.copy()

        fraud_idx = attacked.index[attacked["is_fraud"] == 1]
        count = max(1, int(len(fraud_idx) * fraction))
        selected = self.rng.choice(fraud_idx, count, replace=False)

        attacked.loc[selected, "device_type"] = "unknown"

        return attacked

    def country_change_attack(self, df, fraction=0.25):
        attacked = df.copy()

        fraud_idx = attacked.index[attacked["is_fraud"] == 1]
        count = max(1, int(len(fraud_idx) * fraction))
        selected = self.rng.choice(fraud_idx, count, replace=False)

        attacked.loc[selected, "country"] = self.rng.choice(
            ["RU", "NG", "CN"],
            size=count
        )

        return attacked

    def velocity_attack(self, df, fraction=0.25):
        attacked = df.copy()

        attacked["timestamp"] = pd.to_datetime(
            attacked["timestamp"]
        )

        fraud_idx = attacked.index[attacked["is_fraud"] == 1]
        count = max(1, int(len(fraud_idx) * fraction))
        selected = self.rng.choice(fraud_idx, count, replace=False)

        offsets = pd.to_timedelta(
            self.rng.integers(1, 30, size=count),
            unit="s"
        )

        attacked.loc[selected, "timestamp"] = (
            attacked.loc[selected, "timestamp"].values + offsets
        )

        attacked["timestamp"] = attacked["timestamp"].astype(str)

        return attacked

    def run_all(self, df):
        return {
            "high_value": self.high_value_attack(df),
            "device_change": self.device_change_attack(df),
            "country_change": self.country_change_attack(df),
            "velocity": self.velocity_attack(df),
        }


if __name__ == "__main__":

    df = pd.read_csv("data/raw/transactions.csv")

    red_team = RedTeam()
    attacks = red_team.run_all(df)

    print("=== Red Team Attack Suite ===")

    for name, attacked_df in attacks.items():
        print(
            f"{name}: "
            f"{len(attacked_df)} transactions, "
            f"{attacked_df['is_fraud'].sum()} fraudulent"
        )