# AI/ML Module — Ground Station Security Monitoring

This is the AI/ML component of the AI-Powered Space Ground Station Security
Monitoring Platform. It detects: **DDoS**, **Unauthorized Access/Brute Force**,
**MITM**, **Replay Attacks**, and general **AI-based Telemetry Anomalies**.

## Why two models?

CIC-IDS2017 gives us strong, labeled data for DDoS/DoS and Brute Force, but it
contains **no MITM or Replay samples**. So this module uses two layers:

1. **Supervised classifier** (`train_classifier.py`) — trained on CIC-IDS2017,
   predicts: `BENIGN`, `DDOS`, `BRUTE_FORCE`.
2. **Unsupervised anomaly detector** (`train_anomaly_detector.py`) — trained
   ONLY on benign flows. Flags anything statistically abnormal, which is how
   we catch things we don't have labeled data for, like MITM-style traffic or
   replayed commands, plus any future/unknown attack.

MITM and Replay also get a cheap **rule-based check** (`rules.py`) that your
backend can run directly on live packets/commands (timestamp reuse, duplicate
payload hashes, ARP/MAC-IP mismatches). This is standard practice — signature
checks + ML anomaly detection is more robust than trying to force a generic
flow-based ML model to learn attacks it never saw an example of.

## Setup

```bash
pip install -r requirements.txt
```

Download CIC-IDS2017 CSVs (the "MachineLearningCSV" version, 8 files, one per
day of capture — e.g. from the official UNB site or the Kaggle mirror
"cicids2017") and place them in `data/raw/`.

## Pipeline

```bash
python src/data_loader.py          # merges + cleans raw CSVs -> data/processed/combined.csv
python src/preprocess.py           # encodes, scales, maps labels, splits train/test
python src/train_classifier.py     # trains RandomForest/XGBoost, saves to models/
python src/train_anomaly_detector.py  # trains Isolation Forest on benign-only data
python src/evaluate.py             # prints metrics for both models
```

## Serving

`src/predict_api.py` exposes a single function your backend teammate can call:

```python
from src.predict_api import analyze_flow
result = analyze_flow(flow_features_dict)
# -> {"label": "DDOS", "confidence": 0.94, "is_anomaly": True, "severity": "high"}
```

Wrap this in a FastAPI/Flask endpoint (a minimal example is included at the
bottom of `predict_api.py`) so the backend team can call it over HTTP.

## Feature contract (agree this with Backend team)

Whatever your simulated ground station backend logs per network flow, it must
map to the feature set the model expects — see `FEATURE_COLUMNS` in
`src/config.py`. If your simulation logs different fields, edit that list and
retrain; don't hand-wave a mismatch, or predictions will silently be garbage.
