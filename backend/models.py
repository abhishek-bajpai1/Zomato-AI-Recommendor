"""
Pydantic models for the Zomato Recommender API.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserIn(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Recommendation ─────────────────────────────────────────────────────────────

class PreferencePayload(BaseModel):
    location: Optional[str] = ""
    cuisine: Optional[str] = ""
    price_tier: Optional[str] = ""       # "", "₹", "₹₹", "₹₹₹"
    min_rating: Optional[float] = Field(default=0.0, ge=0.0, le=5.0)


class Restaurant(BaseModel):
    name: str
    location: str
    cuisine: str
    price_tier: str
    rating: float
    reviews: Optional[str] = ""
    review_summary: Optional[str] = ""
