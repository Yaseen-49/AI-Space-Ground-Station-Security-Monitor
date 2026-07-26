"""
Central config: label mapping from raw CIC-IDS2017 labels to our
project's attack categories, plus the feature columns we use.
"""

RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
MODELS_DIR = "models"

# CIC-IDS2017 raw labels -> our 5-category scheme.
# MITM and REPLAY have no direct source in this dataset (see README) -
# they are left out of the supervised classifier and instead caught by
# the anomaly detector + rule-based checks.
LABEL_MAP = {
    "BENIGN": "BENIGN",

    "DDoS": "DDOS",
    "DoS Hulk": "DDOS",
    "DoS GoldenEye": "DDOS",
    "DoS slowloris": "DDOS",
    "DoS Slowhttptest": "DDOS",

    "FTP-Patator": "BRUTE_FORCE",
    "SSH-Patator": "BRUTE_FORCE",
    "Web Attack \x96 Brute Force": "BRUTE_FORCE",
    "Web Attack – Brute Force": "BRUTE_FORCE",

    # Everything else in CIC-IDS2017 (PortScan, Infiltration, Bot,
    # Heartbleed, Web Attack XSS/SQLi) doesn't map cleanly to our 5
    # categories. We fold them into a catch-all "OTHER_ANOMALY" bucket
    # so the classifier still learns "this isn't benign" without us
    # inventing a category we don't actually report on the dashboard.
}
OTHER_ANOMALY_LABEL = "OTHER_ANOMALY"

# Final classes the supervised model predicts
CLASSES = ["BENIGN", "DDOS", "BRUTE_FORCE", OTHER_ANOMALY_LABEL]

# CIC-IDS2017 columns commonly have leading spaces - loader strips them.
# These are the core flow-level features (subset of the ~78 CIC-IDS2017
# columns) that are most predictive and also realistic for a simulated
# ground station's network flow logs to produce.
FEATURE_COLUMNS = [
    "Destination Port",
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Fwd Packet Length Mean",
    "Bwd Packet Length Mean",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Fwd IAT Mean",
    "Bwd IAT Mean",
    "Min Packet Length",
    "Max Packet Length",
    "Packet Length Mean",
    "SYN Flag Count",
    "ACK Flag Count",
    "URG Flag Count",
    "Average Packet Size",
]

LABEL_COLUMN = "Label"
RANDOM_STATE = 42
