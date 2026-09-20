from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.quantpulse_engine import Candle
from app.services.quantpulse_fusion import fuse
from app.services.quantpulse_market import OHLCV, validate_candles

router = APIRouter(prefix="/quantpulse/fusion", tags=["quantpulse-fusion"])


class CandleInput(BaseModel):
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(default=0, ge=0)


class FusionRequest(BaseModel):
    instrument_key: str = Field(min_length=1, max_length=128)
    candles: list[CandleInput] = Field(min_length=20)
    expiry: str = Field(default="current_week", min_length=1, max_length=32)


@router.post("/signal")
async def fusion_signal(request: FusionRequest):
    try:
        normalized = validate_candles([
            OHLCV(
                request.instrument_key,
                c.timestamp,
                c.open,
                c.high,
                c.low,
                c.close,
                c.volume,
            )
            for c in request.candles
        ])
        candles = [Candle(c.open, c.high, c.low, c.close, c.volume) for c in normalized]
        return await fuse(candles, request.instrument_key, request.expiry)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
