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
    cuisines: Optional[list[str]] = Field(default_factory=list)
    min_rating: Optional[float] = Field(default=0.0, ge=0.0, le=5.0)
    max_price: Optional[int] = Field(default=None, ge=0)


class Restaurant(BaseModel):
    name: str
    location: str
    cuisine: str
    cost_for_two: int
    min_price_for_two: Optional[int] = None
    rating: float
    reviews: Optional[str] = ""
    review_summary: Optional[str] = ""
