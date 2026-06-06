"""Training XGBoost Regressor untuk prediksi harga motor bekas."""

import os, sys, json
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib
from supabase import create_client
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from features import create_encoders, save_encoders, engineer_features_training, FEATURE_COLUMNS

load_dotenv()

MODEL_PATH   = os.path.join(os.path.dirname(__file__), 'model.pkl')
METRICS_PATH = os.path.join(os.path.dirname(__file__), 'metrics.json')


def main():
    print("=" * 50)
    print("Motor Price Intelligence - ML Training")
    print("=" * 50)

    # 1. Load data
    print("\nLoading data dari Supabase...")
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
    res = sb.table("motor_listings").select("*").eq("is_valid", True).execute()
    df = pd.DataFrame(res.data)
    print(f"Total data: {len(df)} baris")

    if len(df) < 30:
        print("ERROR: Data terlalu sedikit. Jalankan SQL dummy data dulu.")
        return

    # 2. Clean
    df = df.dropna(subset=['brand', 'model', 'year', 'price'])
    df = df[df['price'].between(1_000_000, 500_000_000)]
    print(f"Setelah cleaning: {len(df)} baris")

    # 3. Encoder + features
    encoders = create_encoders(df)
    X = engineer_features_training(df, encoders)
    y = df['price']

    # 4. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    # 5. Train
    model = XGBRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
        early_stopping_rounds=20, eval_metric='mae',
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)

    # 6. Evaluate
    y_pred = model.predict(X_test)
    r2  = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    print("\n" + "=" * 50)
    print(f"R² Score : {r2:.4f}  (target ≥ 0.80)")
    print(f"MAE      : Rp {mae:,.0f}  (target ≤ Rp 1.500.000)")
    print("=" * 50)

    # 7. Feature importance
    importance = sorted(
        zip(FEATURE_COLUMNS, model.feature_importances_),
        key=lambda x: x[1], reverse=True
    )
    print("\nFeature Importance:")
    for feat, imp in importance:
        bar = '█' * int(imp * 40)
        print(f"  {feat:<25} {bar} {imp:.4f}")

    # 8. Save
    joblib.dump(model, MODEL_PATH)
    save_encoders(encoders)

    metrics = {
        'r2': float(r2), 'mae': float(mae),
        'n_train': len(X_train), 'n_test': len(X_test),
        'feature_importance': [{'feature': f, 'importance': float(i)} for f, i in importance]
    }
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"\nModel tersimpan: {MODEL_PATH}")
    print("Training selesai!")


if __name__ == "__main__":
    main()