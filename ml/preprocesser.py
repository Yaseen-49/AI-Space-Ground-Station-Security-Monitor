"""
Preprocessing: maps raw CIC-IDS2017 labels to our 5-category scheme,
selects features, imputes missing values, scales, and splits into
train/test sets. Saves the fitted scaler so predict_api.py can reuse
the exact same transform at inference time.

Run: python src/preprocess.py
"""
import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

from config import (
    PROCESSED_DATA_DIR,
    MODELS_DIR,
    LABEL_MAP,
    OTHER_ANOMALY_LABEL,
    FEATURE_COLUMNS,
    LABEL_COLUMN,
    RANDOM_STATE,
)


def map_label(raw_label: str) -> str:
    raw_label = raw_label.strip()
    return LABEL_MAP.get(raw_label, OTHER_ANOMALY_LABEL)


def preprocess():
    combined_path = os.path.join(PROCESSED_DATA_DIR, "combined.csv")
    df = pd.read_csv(combined_path, low_memory=False)

    # Map labels to our categories
    df["category"] = df[LABEL_COLUMN].apply(map_label)
    print("Mapped category distribution:")
    print(df["category"].value_counts())

    # Keep only the feature columns we've decided on, plus target
    missing_cols = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Expected columns missing from data: {missing_cols}. "
            f"Check config.FEATURE_COLUMNS against your CSV headers."
        )

    X = df[FEATURE_COLUMNS].copy()
    y = df["category"].copy()

    # Impute missing/inf-replaced values with median (robust to outliers)
    imputer = SimpleImputer(strategy="median")
    X_imputed = pd.DataFrame(
        imputer.fit_transform(X), columns=FEATURE_COLUMNS
    )

    # Scale features
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(
        scaler.fit_transform(X_imputed), columns=FEATURE_COLUMNS
    )

    # Train/test split, stratified since classes are imbalanced
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    X_train.to_csv(os.path.join(PROCESSED_DATA_DIR, "X_train.csv"), index=False)
    X_test.to_csv(os.path.join(PROCESSED_DATA_DIR, "X_test.csv"), index=False)
    y_train.to_csv(os.path.join(PROCESSED_DATA_DIR, "y_train.csv"), index=False)
    y_test.to_csv(os.path.join(PROCESSED_DATA_DIR, "y_test.csv"), index=False)

    joblib.dump(imputer, os.path.join(MODELS_DIR, "imputer.joblib"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "scaler.joblib"))

    print(f"Train shape: {X_train.shape}, Test shape: {X_test.shape}")
    print("Saved processed splits + imputer/scaler to disk.")


if __name__ == "__main__":
    preprocess()
