"""
Single entry point the Backend team calls: analyze_flow(features_dict).

Combines:
  1. Supervised classifier -> BENIGN / DDOS / BRUTE_FORCE / OTHER_ANOMALY
  2. Anomaly detector       -> statistical outlier flag (catches MITM/replay-style deviations)
  3. Rule checks (optional) -> exact MITM/Replay signature checks, if the
     backend also passes command/telemetry event metadata

Run the demo Flask server: python src/predict_api.py
"""
import os
import joblib
import pandas as pd

from config import MODELS_DIR, FEATURE_COLUMNS
from rules import run_rule_checks

_imputer = joblib.load(os.path.join(MODELS_DIR, "imputer.joblib"))
_scaler = joblib.load(os.path.join(MODELS_DIR, "scaler.joblib"))
_classifier = joblib.load(os.path.join(MODELS_DIR, "classifier.joblib"))
_label_encoder = joblib.load(os.path.join(MODELS_DIR, "label_encoder.joblib"))
_anomaly_detector = joblib.load(os.path.join(MODELS_DIR, "anomaly_detector.joblib"))

SEVERITY_MAP = {
    "BENIGN": "none",
    "DDOS": "high",
    "BRUTE_FORCE": "medium",
    "OTHER_ANOMALY": "medium",
}


def _prepare_features(flow_features: dict) -> pd.DataFrame:
    row = {col: flow_features.get(col) for col in FEATURE_COLUMNS}
    df = pd.DataFrame([row])
    df_imputed = pd.DataFrame(_imputer.transform(df), columns=FEATURE_COLUMNS)
    df_scaled = pd.DataFrame(_scaler.transform(df_imputed), columns=FEATURE_COLUMNS)
    return df_scaled


def analyze_flow(flow_features: dict, event_meta: dict = None) -> dict:
    """
    flow_features: dict matching config.FEATURE_COLUMNS (network flow stats)
    event_meta: optional dict for rule-based MITM/Replay checks
                (src_mac, src_ip, payload_hash, timestamp, sequence_number)
    """
    X = _prepare_features(flow_features)

    pred_enc = _classifier.predict(X)[0]
    pred_label = _label_encoder.inverse_transform([pred_enc])[0]
    pred_proba = _classifier.predict_proba(X)[0]
    confidence = float(max(pred_proba))

    is_anomaly = _anomaly_detector.predict(X)[0] == -1

    result = {
        "label": pred_label,
        "confidence": round(confidence, 4),
        "is_anomaly": bool(is_anomaly),
        "severity": SEVERITY_MAP.get(pred_label, "medium") if pred_label != "BENIGN" else "none",
    }

    if event_meta:
        rule_result = run_rule_checks(event_meta)
        result.update(rule_result)
        if rule_result.get("is_mitm_suspect"):
            result["label"] = "MITM_SUSPECT"
            result["severity"] = "high"
        elif rule_result.get("is_replay_suspect"):
            result["label"] = "REPLAY_SUSPECT"
            result["severity"] = "high"

    # If the statistical anomaly detector disagrees with "BENIGN", raise severity
    if result["label"] == "BENIGN" and is_anomaly:
        result["severity"] = "low"
        result["note"] = "Classified benign but flagged as statistical outlier - review recommended"

    return result


# --- Minimal Flask app so the backend team can call this over HTTP ---
if __name__ == "__main__":
    from flask import Flask, request, jsonify

    app = Flask(__name__)

    @app.route("/analyze", methods=["POST"])
    def analyze():
        payload = request.get_json(force=True)
        flow_features = payload.get("flow_features", {})
        event_meta = payload.get("event_meta")
        return jsonify(analyze_flow(flow_features, event_meta))

    app.run(host="0.0.0.0", port=5001, debug=True)
