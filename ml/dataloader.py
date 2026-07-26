"""
Loads the raw CIC-IDS2017 CSV files (one per day of capture), strips
whitespace from column names (a known quirk of this dataset), merges
them, drops obvious junk rows, and writes a single combined CSV.

Run: python src/data_loader.py
"""
import glob
import os
import pandas as pd
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, LABEL_COLUMN


def load_all_csvs(raw_dir: str = RAW_DATA_DIR) -> pd.DataFrame:
    csv_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {raw_dir}. Download CIC-IDS2017 "
            f"'MachineLearningCSV' files and place them there."
        )

    frames = []
    for f in csv_files:
        print(f"Loading {f} ...")
        df = pd.read_csv(f, low_memory=False, encoding="latin1")
        df.columns = [c.strip() for c in df.columns]  # strip leading spaces
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    print(f"Combined shape before cleaning: {combined.shape}")

    # Drop rows with missing label, and replace inf values (common in
    # Flow Bytes/s and Flow Packets/s columns) with NaN so they can be
    # dropped or imputed in preprocessing.
    combined = combined.dropna(subset=[LABEL_COLUMN])
    combined = combined.replace([float("inf"), float("-inf")], pd.NA)

    print(f"Combined shape after cleaning: {combined.shape}")
    print("Label distribution:")
    print(combined[LABEL_COLUMN].value_counts())

    return combined


if __name__ == "__main__":
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    df = load_all_csvs()
    out_path = os.path.join(PROCESSED_DATA_DIR, "combined.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved combined dataset to {out_path}")
