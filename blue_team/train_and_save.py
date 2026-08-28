import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import xgboost as xgb

DATA_PATH = "data/raw/transactions.csv"
ARTIFACT_DIR = "models_saved"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def train_and_export():
    print("1. Loading raw dataset...")
    df = pd.read_csv(DATA_PATH)
    df.columns = [c.strip().lower() for c in df.columns]
    target_col = 'is_fraud' if 'is_fraud' in df.columns else 'fraud'

    time_col = next((c for c in df.columns if 'time' in c or 'date' in c), None)
    if time_col:
        df[time_col] = pd.to_datetime(df[time_col])
        df = df.sort_values(by=time_col).reset_index(drop=True)

    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()

    # Build user baseline profiles strictly on training data
    print("2. Building user baseline profiles...")
    global_avg_amt = float(train_df['amount'].mean())
    global_std_amt = float(train_df['amount'].std()) if train_df['amount'].std() > 0 else 1.0

    user_profiles = train_df.groupby('user_id').agg(
        user_avg_amount=('amount', 'mean'),
        user_std_amount=('amount', 'std'),
        user_txn_count=('amount', 'count'),
        common_country=('country', lambda x: x.mode()[0] if not x.empty else 'UNKNOWN'),
        common_device=('device_type', lambda x: x.mode()[0] if not x.empty else 'UNKNOWN')
    ).reset_index()
    user_profiles['user_std_amount'] = user_profiles['user_std_amount'].fillna(global_std_amt)

    # Feature engineering extraction
    def extract_features(data, profiles):
        d = data.copy()
        d = d.merge(profiles, on='user_id', how='left')
        d['user_avg_amount'] = d['user_avg_amount'].fillna(global_avg_amt)
        d['user_std_amount'] = d['user_std_amount'].fillna(global_std_amt)
        d['user_txn_count'] = d['user_txn_count'].fillna(0)
        d['common_country'] = d['common_country'].fillna('UNKNOWN')
        d['common_device'] = d['common_device'].fillna('UNKNOWN')

        d['log_amount'] = np.log1p(d['amount'])
        d['amount_to_avg_ratio'] = d['amount'] / (d['user_avg_amount'] + 1e-5)
        d['amount_zscore'] = (d['amount'] - d['user_avg_amount']) / (d['user_std_amount'] + 1e-5)
        d['country_changed'] = (d['country'] != d['common_country']).astype(int)
        d['device_changed'] = (d['device_type'] != d['common_device']).astype(int)

        if time_col:
            d['hour'] = d[time_col].dt.hour
            d['day_of_week'] = d[time_col].dt.dayofweek
            d['is_night'] = d['hour'].apply(lambda h: 1 if (h >= 23 or h <= 5) else 0)
            d['seconds_since_prev'] = d.groupby('user_id')[time_col].diff().dt.total_seconds().fillna(86400)
            d['velocity_10m'] = (d['seconds_since_prev'] <= 600).astype(int)
            d['velocity_1h'] = (d['seconds_since_prev'] <= 3600).astype(int)
        else:
            d['hour'] = 12
            d['day_of_week'] = 0
            d['is_night'] = 0
            d['seconds_since_prev'] = 86400
            d['velocity_10m'] = 0
            d['velocity_1h'] = 0

        cat_cols = ['transaction_type', 'country', 'device_type']
        existing_cats = [c for c in cat_cols if c in d.columns]
        d = pd.get_dummies(d, columns=existing_cats, drop_first=True)
        return d

    train_feat = extract_features(train_df, user_profiles)
    drop_cols = [target_col, 'user_id', 'common_country', 'common_device']
    if time_col and time_col in train_feat.columns:
        drop_cols.append(time_col)
    if 'transaction_id' in train_feat.columns:
        drop_cols.append('transaction_id')

    X_train = train_feat.drop(columns=[c for c in drop_cols if c in train_feat.columns]).astype(float)
    y_train = train_feat[target_col]
    feature_columns = list(X_train.columns)

    # Train Supervised Model
    print("3. Training XGBoost Classifier...")
    scale_pos = (len(y_train) - sum(y_train)) / sum(y_train)
    xgb_model = xgb.XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.03,
        scale_pos_weight=scale_pos, subsample=0.8, colsample_bytree=0.8,
        random_state=42, tree_method='hist'
    )
    xgb_model.fit(X_train, y_train)

    # Train Anomaly Detector
    print("4. Training Isolation Forest Anomaly Layer...")
    iso_model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    iso_model.fit(X_train[y_train == 0])

    # Export all artifacts to disk
    print("5. Saving all model artifacts...")
    joblib.dump(xgb_model, os.path.join(ARTIFACT_DIR, "xgb_model.pkl"))
    joblib.dump(iso_model, os.path.join(ARTIFACT_DIR, "iso_model.pkl"))
    user_profiles.to_pickle(os.path.join(ARTIFACT_DIR, "user_profiles.pkl"))
    joblib.dump({
        "feature_columns": feature_columns,
        "global_avg_amt": global_avg_amt,
        "global_std_amt": global_std_amt
    }, os.path.join(ARTIFACT_DIR, "pipeline_meta.pkl"))

    print("SUCCESS: All artifacts successfully saved to models_saved/")

if __name__ == "__main__":
    train_and_export()