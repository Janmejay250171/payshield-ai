import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

from red_team.attacks import RedTeam
from blue_team.ml_detector import FraudDetector

# Standard operational threshold for imbalanced fraud detection
FRAUD_THRESHOLD = 0.15

df = pd.read_csv("data/raw/transactions.csv")

train_df, test_df = train_test_split(
    df,
    test_size=0.20,
    stratify=df["is_fraud"],
    random_state=42
)

detector = FraudDetector()
detector.train(train_df)

print("\n=== HOLDOUT TEST (Threshold = 0.15) ===")

normal = detector.predict(test_df)
normal_pred = (normal["fraud_probability"] >= FRAUD_THRESHOLD).astype(int)

print(
    classification_report(
        test_df["is_fraud"],
        normal_pred,
        digits=4,
        zero_division=0
    )
)

print("\n=== RED TEAM ATTACK EVALUATION ===")

red_team = RedTeam()
attacks = red_team.run_all(test_df)

for name, attacked_df in attacks.items():
    results = detector.predict(attacked_df)
    actual = attacked_df["is_fraud"]
    predicted = (results["fraud_probability"] >= FRAUD_THRESHOLD).astype(int)

    print(f"\n{name.upper()}")
    print(
        classification_report(
            actual,
            predicted,
            digits=4,
            zero_division=0
        )
    )