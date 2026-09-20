from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.quantpulse_engine import Candle, analyze

router = APIRouter(prefix="/quantpulse", tags=["quantpulse"])


class CandleInput(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class SignalRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    candles: list[CandleInput] = Field(min_length=20)
    news_sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)


@router.get("/health")
async def quantpulse_health() -> dict:
    return {
        "service": "quantpulse",
        "status": "ready",
        "mode": "analysis-only",
        "live_execution": False,
    }


@router.post("/signal")
async def quantpulse_signal(request: SignalRequest) -> dict:
    try:
        result = analyze(
            [Candle(c.open, c.high, c.low, c.close, c.volume) for c in request.candles],
            request.news_sentiment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "symbol": request.symbol.upper(),
        "engine": "QuantPulse Fusion v1",
        "result": result,
    }
