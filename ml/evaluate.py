"""
Evaluates the classifier and anomaly detector on the held-out test set.
Prints classification report + confusion matrix, and anomaly detector
flag-rate on benign vs attack test samples (sanity check: it should
flag attacks far more often than benign traffic).

Run: python src/evaluate.py
"""
import os
import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

from config import PROCESSED_DATA_DIR, MODELS_DIR


def evaluate():
    X_test = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "X_test.csv"))
    y_test = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "y_test.csv")).squeeze()

    classifier = joblib.load(os.path.join(MODELS_DIR, "classifier.joblib"))
    label_encoder = joblib.load(os.path.join(MODELS_DIR, "label_encoder.joblib"))
    anomaly_detector = joblib.load(os.path.join(MODELS_DIR, "anomaly_detector.joblib"))

    # --- Classifier evaluation ---
    y_pred_enc = classifier.predict(X_test)
    y_pred = label_encoder.inverse_transform(y_pred_enc)

    print("=" * 60)
    print("SUPERVISED CLASSIFIER REPORT")
    print("=" * 60)
    print(classification_report(y_test, y_pred, zero_division=0))
    print("Confusion matrix (rows=actual, cols=predicted):")
    labels_sorted = sorted(y_test.unique())
    print(pd.DataFrame(
        confusion_matrix(y_test, y_pred, labels=labels_sorted),
        index=labels_sorted, columns=labels_sorted,
    ))

    # --- Anomaly detector sanity check ---
    print("\n" + "=" * 60)
    print("ANOMALY DETECTOR FLAG RATE (should be low for BENIGN, high for attacks)")
    print("=" * 60)
    preds = anomaly_detector.predict(X_test)  # -1 = anomaly, 1 = normal
    flagged = pd.Series(preds == -1, index=X_test.index)

    for cls in sorted(y_test.unique()):
        mask = y_test == cls
        rate = flagged[mask].mean() if mask.sum() > 0 else float("nan")
        print(f"  {cls:15s} flagged as anomaly: {rate:.1%}  (n={mask.sum()})")


if __name__ == "__main__":
    evaluate()
