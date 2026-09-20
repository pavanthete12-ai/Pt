from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.quantpulse_engine import Candle, analyze
from app.services.quantpulse_market import OHLCV, validate_candles

router = APIRouter(prefix="/quantpulse", tags=["quantpulse"])

class CandleInput(BaseModel):
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(default=0, ge=0)

class SignalRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    candles: list[CandleInput] = Field(min_length=20)
    news_sentiment: float = Field(default=0.0, ge=-1, le=1)

@router.get("/health")
async def health():
    return {"service":"QuantPulse","mode":"analysis-only","live_execution":False}

@router.post("/signal")
async def signal(request: SignalRequest):
    try:
        normalized = validate_candles([OHLCV(request.symbol,c.timestamp,c.open,c.high,c.low,c.close,c.volume) for c in request.candles])
        result = analyze([Candle(c.open,c.high,c.low,c.close,c.volume) for c in normalized], news_sentiment=request.news_sentiment)
        return {"symbol":request.symbol.upper(),"engine":"QuantPulse Fusion v1","result":result}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.post("/validate-candles")
async def validate_market_candles(symbol: str, candles: list[CandleInput]):
    try:
        normalized = validate_candles([OHLCV(symbol,c.timestamp,c.open,c.high,c.low,c.close,c.volume) for c in candles])
        return {"symbol":symbol.upper(),"count":len(normalized),"first":normalized[0].timestamp if normalized else None,"last":normalized[-1].timestamp if normalized else None,"data_quality":"OK"}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
