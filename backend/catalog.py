"""
Restaurant catalog: loads data/zomato_cleaned.csv and provides filter helpers.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

import pandas as pd

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "zomato_cleaned.csv"

_df: Optional[pd.DataFrame] = None


def _load() -> pd.DataFrame:
    global _df
    if _df is None:
        if not _DATA_PATH.exists():
            raise FileNotFoundError(
                f"Cleaned data not found at {_DATA_PATH}. "
                "Run: python data_pipeline/explore_and_clean_data.py"
            )
        # Explicit UTF-8 for Windows compatibility with "₹"
        _df = pd.read_csv(_DATA_PATH, encoding="utf-8")
        # Normalise strings
        for col in ("location", "cuisine", "name", "reviews"):
            _df[col] = _df[col].fillna("").astype(str).str.strip()
        _df["rating"] = pd.to_numeric(_df["rating"], errors="coerce").fillna(0.0)
        _df["cost_for_two"] = pd.to_numeric(_df["cost_for_two"], errors="coerce").fillna(500).astype(int)
    return _df


def get_locations() -> list[str]:
    df = _load()
    # Now that the pipeline correctly maps neighborhood to 'location',
    # we can just take the unique sorted list.
    locs = sorted(df["location"].unique().tolist())
    return [l.title() for l in locs if l]


def get_cuisines() -> list[str]:
    df = _load()
    unique_c = set()
    for val in df["cuisine"].str.lower().str.split(", "):
        for c in val:
            if c.strip():
                unique_c.add(c.strip())
    return sorted(list(unique_c))


def filter_restaurants(
    location: str,
    cuisines: list[str],
    min_rating: float,
    limit: int = 50,
) -> pd.DataFrame:
    df = _load().copy()

    if location and location.strip():
        df = df[df["location"].str.contains(location.strip().lower(), case=False, na=False)]

    if cuisines:
        # Filter for any of the selected cuisines
        mask = pd.Series(False, index=df.index)
        for c in cuisines:
            if c.strip():
                mask |= df["cuisine"].str.contains(c.strip().lower(), case=False, na=False)
        df = df[mask]

    if min_rating and min_rating > 0:
        df = df[df["rating"] >= min_rating]

    # Default sort: rating desc, name asc
    df = df.sort_values(["rating", "name"], ascending=[False, True])
    return df.head(limit)
