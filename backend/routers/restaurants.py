"""
Restaurants router: GET /restaurants/locations, /restaurants/cuisines, POST /recommendations
"""

from __future__ import annotations
from fastapi import APIRouter, Depends

from backend.catalog import filter_restaurants, get_locations, get_cuisines
from backend.models import PreferencePayload, Restaurant
from backend.routers.auth import get_current_user
from backend import groq_ranker

router = APIRouter(tags=["restaurants"])


@router.get("/restaurants/locations", response_model=list[str])
def list_locations(_: str = Depends(get_current_user)):
    return get_locations()


@router.get("/restaurants/cuisines", response_model=list[str])
def list_cuisines(_: str = Depends(get_current_user)):
    return get_cuisines()


@router.post("/recommendations", response_model=list[Restaurant])
def recommendations(
    payload: PreferencePayload,
    email: str = Depends(get_current_user),
):
    df = filter_restaurants(
        location=payload.location or "",
        cuisines=payload.cuisines or [],
        min_rating=payload.min_rating or 0.0,
    )

    results = [
        Restaurant(
            name=row["name"],
            location=row["location"],
            cuisine=row["cuisine"],
            cost_for_two=int(row["cost_for_two"]),
            rating=float(row["rating"]),
            reviews=row.get("reviews", ""),
        )
        for _, row in df.iterrows()
    ]

    # Groq re-ranking (falls back gracefully if key missing)
    results = groq_ranker.rerank(results, payload.model_dump())
    return results
