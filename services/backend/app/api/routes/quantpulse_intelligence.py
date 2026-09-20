from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services.quantpulse_intelligence import get_intelligence_service

router = APIRouter(prefix="/quantpulse/intelligence", tags=["quantpulse-intelligence"])


@router.get("/{instrument_key:path}")
async def intelligence_snapshot(
    instrument_key: str,
    expiry: str = Query("current_week", min_length=1, max_length=32),
    include_news: bool = True,
):
    if not instrument_key.strip():
        raise HTTPException(status_code=422, detail="instrument_key is required")
    return await get_intelligence_service().snapshot(
        instrument_key=instrument_key,
        expiry=expiry,
        include_news=include_news,
    )
