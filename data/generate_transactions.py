import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


random.seed(42)
np.random.seed(42)

N_TRANSACTIONS = 20000
N_USERS = 2000


def generate_transactions(n=N_TRANSACTIONS):

    start_time = datetime.now() - timedelta(days=30)

    users = {}

    # ---------------------------------------------------------
    # 1. Create normal user profiles
    # ---------------------------------------------------------

    for i in range(1, N_USERS + 1):

        users[f"USER{i:05d}"] = {
            "avg_amount": np.random.uniform(100, 1200),
            "country": np.random.choice(
                ["IN", "IN", "IN", "IN", "US", "GB", "SG"]
            ),
            "device": np.random.choice(
                ["mobile", "desktop", "tablet"]
            ),
            "transaction_type": np.random.choice(
                ["UPI", "CARD", "NETBANKING", "WALLET"]
            ),
        }

    rows = []

    # ---------------------------------------------------------
    # 2. Generate normal transactions
    # ---------------------------------------------------------

    for i in range(n):

        user_id = random.choice(list(users.keys()))
        profile = users[user_id]

        timestamp = start_time + timedelta(
            seconds=random.randint(
                0,
                30 * 24 * 60 * 60
            )
        )

        amount = max(
            5,
            np.random.normal(
                profile["avg_amount"],
                profile["avg_amount"] * 0.30
            )
        )

        rows.append(
            {
                "transaction_id": f"TXN{i + 1:08d}",
                "user_id": user_id,
                "timestamp": timestamp,
                "amount": round(amount, 2),
                "transaction_type": profile["transaction_type"],
                "country": profile["country"],
                "device_type": profile["device"],
                "is_fraud": 0,
            }
        )

    df = pd.DataFrame(rows)

    # ---------------------------------------------------------
    # 3. Sort chronologically
    # ---------------------------------------------------------

    df = df.sort_values("timestamp").reset_index(drop=True)

    # ---------------------------------------------------------
    # 4. Select fraudulent transactions
    # ---------------------------------------------------------

    fraud_count = int(n * 0.05)

    fraud_indices = np.random.choice(
        df.index,
        size=fraud_count,
        replace=False
    )

    df.loc[fraud_indices, "is_fraud"] = 1

    # ---------------------------------------------------------
    # 5. Fraud Pattern: Amount anomaly
    # ---------------------------------------------------------

    amount_count = int(fraud_count * 0.40)

    amount_idx = np.random.choice(
        fraud_indices,
        size=amount_count,
        replace=False
    )

    df.loc[amount_idx, "amount"] *= np.random.uniform(
        4,
        12,
        size=amount_count
    )

    # ---------------------------------------------------------
    # 6. Fraud Pattern: Device takeover
    # ---------------------------------------------------------

    device_count = int(fraud_count * 0.35)

    device_idx = np.random.choice(
        fraud_indices,
        size=device_count,
        replace=False
    )

    df.loc[device_idx, "device_type"] = "unknown"

    # ---------------------------------------------------------
    # 7. Fraud Pattern: Geographic anomaly
    # ---------------------------------------------------------

    country_count = int(fraud_count * 0.30)

    country_idx = np.random.choice(
        fraud_indices,
        size=country_count,
        replace=False
    )

    df.loc[country_idx, "country"] = np.random.choice(
        ["RU", "NG", "CN"],
        size=country_count
    )

    # ---------------------------------------------------------
    # 8. Fraud Pattern: Night-time activity
    # ---------------------------------------------------------

    night_count = int(fraud_count * 0.30)

    night_idx = np.random.choice(
        fraud_indices,
        size=night_count,
        replace=False
    )

    for idx in night_idx:

        old_timestamp = df.loc[idx, "timestamp"]

        night_hour = random.choice(
            [0, 1, 2, 3, 4, 23]
        )

        df.loc[idx, "timestamp"] = old_timestamp.replace(
            hour=night_hour,
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )

    # ---------------------------------------------------------
    # 9. Fraud Pattern: High velocity
    # ---------------------------------------------------------

    velocity_count = int(fraud_count * 0.35)

    velocity_idx = np.random.choice(
        fraud_indices,
        size=velocity_count,
        replace=False
    )

    for idx in velocity_idx:

        base_time = pd.to_datetime(
            df.loc[idx, "timestamp"]
        )

        df.loc[idx, "timestamp"] = (
            base_time
            + timedelta(
                seconds=random.randint(1, 20)
            )
        )

    # ---------------------------------------------------------
    # 10. Fraud Pattern: Transaction channel anomaly
    # ---------------------------------------------------------

    channel_count = int(fraud_count * 0.25)

    channel_idx = np.random.choice(
        fraud_indices,
        size=channel_count,
        replace=False
    )

    df.loc[channel_idx, "transaction_type"] = "NETBANKING"

    # ---------------------------------------------------------
    # Final ordering
    # ---------------------------------------------------------

    df = df.sort_values("timestamp").reset_index(drop=True)

    return df


if __name__ == "__main__":

    df = generate_transactions()

    output = "data/raw/transactions.csv"

    df.to_csv(output, index=False)

    print("=== PayShield Synthetic Dataset ===")
    print(f"Transactions : {len(df)}")
    print(f"Users        : {df['user_id'].nunique()}")
    print(f"Fraud        : {df['is_fraud'].sum()}")
    print(
        f"Fraud rate   : "
        f"{df['is_fraud'].mean():.2%}"
    )
    print(f"Saved to     : {output}")