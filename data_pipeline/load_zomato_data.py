"""
Step 1: Load Zomato dataset from Kaggle for the AI Restaurant Recommendation System.
Uses kagglehub to download and load the dataset as a pandas DataFrame.

Prerequisites:
  pip install "kagglehub[pandas-datasets]" pandas

Kaggle API (for local runs):
  Place kaggle.json in ~/.kaggle/ or set KAGGLE_USERNAME and KAGGLE_KEY.
  See: https://github.com/Kaggle/kaggle-api
"""

import os
import sys
import csv

# Increase field size limit for large reviews in Zomato dataset
csv.field_size_limit(10**6)

# Optional: use pathlib for path handling
try:
    import kagglehub
    from kagglehub import KaggleDatasetAdapter
    import pandas as pd
except ImportError as e:
    print("Missing dependency. Install with: pip install 'kagglehub[pandas-datasets]' pandas", file=sys.stderr)
    raise

# Dataset identifier
DATASET_OWNER = "rajeshrampure"
DATASET_NAME = "zomato-dataset"
DATASET_SLUG = f"{DATASET_OWNER}/{DATASET_NAME}"

# Set the path to the file you want to load inside the dataset.
# Common names: "zomato.csv", "Zomato data.csv", or "" to try default.
# Check the dataset page on Kaggle for exact filenames: https://www.kaggle.com/datasets/rajeshrampure/zomato-dataset
FILE_PATH = "zomato.csv"


def load_via_adapter(file_path: str):
    """Load dataset using KaggleDatasetAdapter.PANDAS."""
    df = kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        DATASET_SLUG,
        file_path,
    )
    return df


def load_via_download():
    """
    Fallback: download dataset and load first CSV found.
    Use this if load_via_adapter fails (e.g. wrong file_path or adapter behavior).
    """
    dataset_path = kagglehub.dataset_download(DATASET_SLUG)
    csv_files = list(os.path.join(dataset_path, f) for f in os.listdir(dataset_path) if f.lower().endswith(".csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV file found under {dataset_path}. List dir: {os.listdir(dataset_path)}")
    path = csv_files[0]
    if len(csv_files) > 1:
        print(f"Multiple CSVs found; using: {path}", file=sys.stderr)
    return pd.read_csv(path, engine='python', on_bad_lines='skip', nrows=10000)


def main():
    file_path = FILE_PATH.strip()
    df = None

    if file_path:
        try:
            df = load_via_adapter(file_path)
        except Exception as e:
            print(f"Adapter load failed ({e}). Trying download fallback...", file=sys.stderr)
            df = load_via_download()
    else:
        try:
            # Some adapters accept "" for default/first file
            df = load_via_adapter("")
        except Exception:
            df = load_via_download()

    print("First 5 records:")
    print(df.head())
    print("\nColumns:", list(df.columns))
    print("\nShape:", df.shape)
    print("\n--- Preference column mapping (Location, Cuisine, Price, Ratings) ---")
    suggest_mapping(df)
    return df


def get_preference_mapping(df: "pd.DataFrame") -> dict:
    """Return a dict mapping preference names to dataset column names. Used by Step 2."""
    mapping = {}
    for key in ("location", "locality", "area", "address", "city", "address line"):
        cand = [c for c in df.columns if key in c.lower()]
        if cand:
            mapping["Location"] = cand[0]
            break
    if "Location" not in mapping:
        mapping["Location"] = None
    for key in ("cuisine", "cuisines", "type", "food type"):
        cand = [c for c in df.columns if key in c.lower()]
        if cand:
            mapping["Cuisine"] = cand[0]
            break
    if "Cuisine" not in mapping:
        mapping["Cuisine"] = None
    for key in ("cost", "price", "average_cost", "price_range", "budget"):
        cand = [c for c in df.columns if key in c.lower()]
        if cand:
            mapping["Price"] = cand[0]
            break
    if "Price" not in mapping:
        mapping["Price"] = None
    for key in ("rating", "rate", "aggregate", "review"):
        cand = [c for c in df.columns if key in c.lower()]
        if cand:
            mapping["Ratings"] = cand[0]
            break
    if "Ratings" not in mapping:
        mapping["Ratings"] = None
    for key in ("name", "restaurant", "title"):
        cand = [c for c in df.columns if key in c.lower() and "id" not in c.lower()]
        if cand:
            mapping["Name"] = cand[0]
            break
    if "Name" not in mapping:
        mapping["Name"] = None
    return mapping


def suggest_mapping(df: "pd.DataFrame") -> None:
    """Print dataset columns that map to our 4 preferences: Location, Cuisine, Price, Ratings."""
    mapping = get_preference_mapping(df)
    for pref, col in mapping.items():
        print(f"  {pref}  ->  {col or '(none found – check columns above)'}")


if __name__ == "__main__":
    main()
