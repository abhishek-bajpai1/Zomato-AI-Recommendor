"""
Restaurant catalog: loads data/zomato_cleaned.csv and provides filter helpers.
Uses robust path resolution for Vercel serverless (cwd may differ from __file__).
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

import pandas as pd

def _resolve_data_path() -> Path:
    """Resolve path to zomato_cleaned.csv - works on local dev and Vercel serverless."""
    # Priority 1: Relative to this file (likely when running as a module)
    base_dir = Path(__file__).resolve().parent.parent
    p = base_dir / "data" / "zomato_cleaned.csv"
    if p.exists():
        return p

    # Priority 2: Relative to current working directory (Vercel often sets this to project root)
    p = Path.cwd() / "data" / "zomato_cleaned.csv"
    if p.exists():
        return p

    # Fallback to current directory for edge cases
    return Path("data/zomato_cleaned.csv").absolute()


_df: Optional[pd.DataFrame] = None


def _load() -> pd.DataFrame:
    global _df
    if _df is None:
        _path = _resolve_data_path()
        if not _path.exists():
            # Return empty DataFrame instead of raising (Vercel: file may be excluded)
            _df = pd.DataFrame(columns=["name", "location", "cuisine", "cost_for_two", "rating", "reviews"])
        else:
            # Explicit UTF-8 for Windows compatibility with "₹"
            _df = pd.read_csv(_path, encoding="utf-8")
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
