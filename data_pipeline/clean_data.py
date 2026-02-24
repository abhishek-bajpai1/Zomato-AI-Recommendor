"""
Step 2: Cleaning logic for Zomato data. Pure functions for testing.
Input: raw DataFrame + column mapping. Output: cleaned DataFrame with standard columns.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

# Standard output column names for the recommendation system
OUT_LOCATION = "location"
OUT_CUISINE = "cuisine"
OUT_COST_FOR_TWO = "cost_for_two"
OUT_RATING = "rating"
OUT_NAME = "name"
OUT_REVIEWS = "reviews"

VALID_PRICE_TIERS = ("₹", "₹₹", "₹₹₹")
MIN_RATING = 0.0
MAX_RATING = 5.0


def _normalize_string(s: Any) -> str:
    """Strip, lowercase, collapse whitespace. NaT/NaN become empty string then dropped later."""
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _cost_to_tier(cost: Any) -> str:
    """Map numeric cost (for two) to price tier ₹, ₹₹, ₹₹₹. Default ₹₹ if invalid."""
    try:
        val = float(cost)
    except (TypeError, ValueError):
        return "₹₹"
    if val <= 0:
        return "₹₹"
    if val < 400:
        return "₹"
    if val < 800:
        return "₹₹"
    return "₹₹₹"


def clean_zomato_df(
    df: pd.DataFrame,
    column_mapping: dict[str, str | None],
) -> pd.DataFrame:
    """
    Clean raw Zomato DataFrame using the given column mapping.
    Returns a DataFrame with columns: name, location, cuisine, price_tier, rating.
    Drops rows where location, cuisine, or rating are missing after cleaning.
    """
    mapping = {k: v for k, v in column_mapping.items() if v is not None and v in df.columns}
    if not mapping:
        return pd.DataFrame(columns=[OUT_NAME, OUT_LOCATION, OUT_CUISINE, OUT_PRICE_TIER, OUT_RATING])

    out = pd.DataFrame()

    # Name
    if "Name" in mapping:
        out[OUT_NAME] = df[mapping["Name"]].fillna("").astype(str).str.strip()
    else:
        out[OUT_NAME] = ["Unknown"] * len(df)

    # Location: normalize
    if "Location" in mapping:
        out[OUT_LOCATION] = df[mapping["Location"]].apply(_normalize_string)
    else:
        out[OUT_LOCATION] = ""

    # Cuisine: normalize (take first cuisine if comma-separated)
    if "Cuisine" in mapping:
        raw = df[mapping["Cuisine"]].apply(_normalize_string)
        out[OUT_CUISINE] = raw.str.split(",").str[0].str.strip().replace("", pd.NA)
    else:
        out[OUT_CUISINE] = pd.NA

    # Cost for two: numeric extraction
    if "Price" in mapping:
        col = mapping["Price"]
        # Convert to string first to handle comma in "1,200"
        cost_series = df[col].astype(str).str.replace(",", "").str.extract(r"(\d+)")[0]
        out[OUT_COST_FOR_TWO] = pd.to_numeric(cost_series, errors="coerce").fillna(500).astype(int)
    else:
        out[OUT_COST_FOR_TWO] = 500

    # Rating: coerce to float, clamp to [MIN_RATING, MAX_RATING]
    # The Zomato dataset stores ratings as "4.1/5" – strip "/5" and non-numeric text first.
    if "Ratings" in mapping:
        rating_series = df[mapping["Ratings"]].astype(str).str.strip()
        # Remove suffix like "/5" or "/10"
        rating_series = rating_series.str.replace(r"/\d+", "", regex=True).str.strip()
        # Coerce anything that's not a number (e.g. "NEW", "-", "nan") to NaN
        raw_rating = pd.to_numeric(rating_series, errors="coerce")
        out[OUT_RATING] = raw_rating.clip(lower=MIN_RATING, upper=MAX_RATING)
    else:
        out[OUT_RATING] = pd.NA

    # Reviews: Truncate to save space
    if "reviews_list" in df.columns:
        out[OUT_REVIEWS] = df["reviews_list"].fillna("").astype(str).str[:1000]
    else:
        out[OUT_REVIEWS] = ""

    # Drop rows missing rating (required for recommendations)
    out = out.dropna(subset=[OUT_RATING])
    # Drop rows where both location and cuisine are empty
    out = out[~(out[OUT_LOCATION].eq("") & out[OUT_CUISINE].isna())]
    # Drop duplicates (same name + location + cuisine)
    out = out.drop_duplicates(subset=[OUT_NAME, OUT_LOCATION, OUT_CUISINE], keep="first")
    out = out.reset_index(drop=True)

    # Ensure rating nulls filled for remaining rows (should be rare)
    out[OUT_RATING] = out[OUT_RATING].fillna(0.0)
    out[OUT_COST_FOR_TWO] = out[OUT_COST_FOR_TWO].fillna(500)

    return out[[OUT_NAME, OUT_LOCATION, OUT_CUISINE, OUT_COST_FOR_TWO, OUT_RATING, OUT_REVIEWS]]
