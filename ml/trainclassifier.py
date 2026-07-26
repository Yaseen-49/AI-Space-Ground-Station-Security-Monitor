"""
Trains the supervised classifier (BENIGN / DDOS / BRUTE_FORCE / OTHER_ANOMALY)
using XGBoost, with class weighting to handle imbalance (BENIGN vastly
outnumbers attack samples in CIC-IDS2017).

Run: python src/train_classifier.py
"""
import os
import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from config import PROCESSED_DATA_DIR, MODELS_DIR, CLASSES, RANDOM_STATE


def train():
    X_train = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "X_train.csv"))
    y_train = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "y_train.csv")).squeeze()

    # Encode string labels to integers for XGBoost
    label_encoder = LabelEncoder()
    label_encoder.fit(CLASSES)  # fix class order so it's consistent at inference
    y_train_enc = label_encoder.transform(y_train)

    model = XGBClassifier(
        n_estimators=300,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="multi:softprob",
        num_class=len(CLASSES),
        eval_metric="mlogloss",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    print("Training XGBoost classifier...")
    model.fit(X_train, y_train_enc)

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(MODELS_DIR, "classifier.joblib"))
    joblib.dump(label_encoder, os.path.join(MODELS_DIR, "label_encoder.joblib"))
    print("Saved classifier.joblib and label_encoder.joblib")


if __name__ == "__main__":
    train()
