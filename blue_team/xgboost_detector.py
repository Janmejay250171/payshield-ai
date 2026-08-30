import pandas as pd
import numpy as np
from sklearn.metrics import (
    classification_report, roc_auc_score, average_precision_score,
    confusion_matrix
)
import xgboost as xgb

DATA_PATH = "data/raw/transactions.csv"

def run_xgboost_pipeline():
    print("Loading PayShield dataset...")
    df = pd.read_csv(DATA_PATH)
    
    # 1. Normalize Column Names
    df.columns = [c.strip().lower() for c in df.columns]
    target_col = 'is_fraud' if 'is_fraud' in df.columns else 'fraud'
    
    # 2. Identify Timestamp and Sort Chronologically
    time_col = next((c for c in df.columns if 'time' in c or 'date' in c), None)
    if time_col:
        df[time_col] = pd.to_datetime(df[time_col])
        df = df.sort_values(by=time_col).reset_index(drop=True)
        print(f"Dataset sorted chronologically using '{time_col}'.")

    # 3. Time-Aware Chronological Split (80% Train, 20% Test)
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    
    print(f"Train size: {len(train_df)} (Fraud: {train_df[target_col].sum()})")
    print(f"Test size:  {len(test_df)} (Fraud: {test_df[target_col].sum()})")

    # 4. Compute User Baselines (STRICTLY on train_df to prevent leakage)
    global_avg_amt = train_df['amount'].mean()
    global_std_amt = train_df['amount'].std() if train_df['amount'].std() > 0 else 1.0

    user_profiles = train_df.groupby('user_id').agg(
        user_avg_amount=('amount', 'mean'),
        user_std_amount=('amount', 'std'),
        user_txn_count=('amount', 'count'),
        common_country=('country', lambda x: x.mode()[0] if not x.empty else 'UNKNOWN'),
        common_device=('device_type', lambda x: x.mode()[0] if not x.empty else 'UNKNOWN')
    ).reset_index()

    user_profiles['user_std_amount'] = user_profiles['user_std_amount'].fillna(global_std_amt)

    # 5. Feature Engineering Function
    def engineer_features(data, profiles):
        d = data.copy()
        d = d.merge(profiles, on='user_id', how='left')

        # Imputation for unseen users in test
        d['user_avg_amount'] = d['user_avg_amount'].fillna(global_avg_amt)
        d['user_std_amount'] = d['user_std_amount'].fillna(global_std_amt)
        d['user_txn_count'] = d['user_txn_count'].fillna(0)
        d['common_country'] = d['common_country'].fillna('UNKNOWN')
        d['common_device'] = d['common_device'].fillna('UNKNOWN')

        # Mathematical and Deviation Features
        d['log_amount'] = np.log1p(d['amount'])
        d['amount_to_avg_ratio'] = d['amount'] / (d['user_avg_amount'] + 1e-5)
        d['amount_zscore'] = (d['amount'] - d['user_avg_amount']) / (d['user_std_amount'] + 1e-5)
        
        d['country_changed'] = (d['country'] != d['common_country']).astype(int)
        d['device_changed'] = (d['device_type'] != d['common_device']).astype(int)

        if time_col:
            d['hour'] = d[time_col].dt.hour
            d['day_of_week'] = d[time_col].dt.dayofweek
            d['is_night'] = d['hour'].apply(lambda h: 1 if (h >= 23 or h <= 5) else 0)
            
            # Inter-transaction delta per user
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

        # One-Hot Encoding
        cat_cols = ['transaction_type', 'country', 'device_type']
        existing_cats = [c for c in cat_cols if c in d.columns]
        d = pd.get_dummies(d, columns=existing_cats, drop_first=True)

        return d

    # Apply feature engineering
    train_feat = engineer_features(train_df, user_profiles)
    test_feat = engineer_features(test_df, user_profiles)

    # 6. Feature Matrix Alignment
    drop_cols = [target_col, 'user_id', 'common_country', 'common_device']
    if time_col and time_col in train_feat.columns:
        drop_cols.append(time_col)
    if 'transaction_id' in train_feat.columns:
        drop_cols.append('transaction_id')

    X_train = train_feat.drop(columns=[c for c in drop_cols if c in train_feat.columns])
    y_train = train_feat[target_col]

    X_test = test_feat.drop(columns=[c for c in drop_cols if c in test_feat.columns])
    y_test = test_feat[target_col]

    # Ensure identical column structure
    X_train, X_test = X_train.align(X_test, join='left', axis=1, fill_value=0)
    X_train = X_train.astype(float)
    X_test = X_test.astype(float)

    print(f"\nFinal feature count: {X_train.shape[1]}")

    # 7. Model Training with Imbalance Weighting
    scale_pos = (len(y_train) - sum(y_train)) / sum(y_train)
    
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.03,
        scale_pos_weight=scale_pos,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric=['logloss', 'aucpr'],
        random_state=42,
        tree_method='hist'
    )

    print("\nTraining XGBoost model...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        verbose=False
    )

    # 8. Evaluation
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    roc_auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)

    print("\n" + "="*60)
    print("XGBOOST BENCHMARK RESULTS (Threshold = 0.50)")
    print("="*60)
    print(classification_report(y_test, y_pred, digits=4))
    print(f"ROC-AUC : {roc_auc:.4f}")
    print(f"PR-AUC  : {pr_auc:.4f}")
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # 9. Threshold Sweep
    print("\n" + "="*60)
    print("THRESHOLD OPTIMIZATION SWEEP")
    print("="*60)
    print("Thresh | Precision | Recall | F1-Score | False Positives")
    print("-" * 55)
    for thresh in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        preds = (y_prob >= thresh).astype(int)
        cm = confusion_matrix(y_test, preds)
        prec = cm[1, 1] / (cm[1, 1] + cm[0, 1]) if (cm[1, 1] + cm[0, 1]) > 0 else 0
        rec = cm[1, 1] / (cm[1, 1] + cm[1, 0]) if (cm[1, 1] + cm[1, 0]) > 0 else 0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0
        fp = cm[0, 1]
        print(f"{thresh:6.2f} | {prec*100:8.2f}% | {rec*100:6.2f}% | {f1*100:7.2f}% | {fp:15d}")

if __name__ == "__main__":
    run_xgboost_pipeline()