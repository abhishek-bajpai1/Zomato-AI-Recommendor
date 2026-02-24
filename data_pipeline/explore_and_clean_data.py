"""
Step 2: Data exploration and cleaning for the AI Restaurant Recommendation System.
Loads Zomato data (from Step 1), inspects it, cleans it, and exports to data/zomato_cleaned.csv.
"""

import os
import sys

# Allow importing from same package
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import pandas as pd

from clean_data import clean_zomato_df
from load_zomato_data import (
    FILE_PATH,
    get_preference_mapping,
    load_via_adapter,
    load_via_download,
)


def load_raw_df():
    """Load raw Zomato DataFrame (reuse Step 1 logic)."""
    file_path = FILE_PATH.strip()
    if file_path:
        try:
            return load_via_adapter(file_path)
        except Exception as e:
            print(f"Adapter load failed ({e}). Trying download fallback...", file=sys.stderr)
            return load_via_download()
    try:
        return load_via_adapter("")
    except Exception:
        return load_via_download()


def explore(df: pd.DataFrame) -> None:
    """Print shape, dtypes, nulls."""
    print("=== Exploration ===")
    print("Shape:", df.shape)
    print("\nDtypes:")
    print(df.dtypes)
    print("\nNull counts:")
    print(df.isnull().sum())
    print("\nSample (first 3 rows):")
    print(df.head(3))


def main():
    print("Loading raw dataset...")
    df = load_raw_df()
    explore(df)

    mapping = get_preference_mapping(df)
    print("\n--- Column mapping for preferences ---")
    for k, v in mapping.items():
        print(f"  {k} -> {v}")

    print("\nCleaning...")
    cleaned = clean_zomato_df(df, mapping)
    print(f"Cleaned shape: {cleaned.shape}")
    
    # Rating range:
    print(f"Rating range: {cleaned['rating'].min()} - {cleaned['rating'].max()}")

    # Export to data/zomato_cleaned.csv (project root = parent of scripts/)
    project_root = os.path.dirname(SCRIPT_DIR)
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    out_path = os.path.join(data_dir, "zomato_cleaned.csv")
    cleaned.to_csv(out_path, index=False)
    print(f"\nExported to {out_path}")
    return cleaned


if __name__ == "__main__":
    main()
