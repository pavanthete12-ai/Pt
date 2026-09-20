from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.quantpulse_backtest import run_backtest
from app.services.quantpulse_engine import Candle

router = APIRouter(prefix="/quantpulse/backtest", tags=["quantpulse-backtest"])

class BacktestCandle(BaseModel):
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0, default=0)

class BacktestRequest(BaseModel):
    candles: list[BacktestCandle] = Field(min_length=30)
    initial_capital: float = Field(gt=0, default=100000)
    risk_fraction: float = Field(gt=0, le=1, default=0.01)
    fee_bps: float = Field(ge=0, default=5)
    slippage_bps: float = Field(ge=0, default=2)

@router.post("")
async def backtest(request: BacktestRequest):
    try:
        result = run_backtest(
            [Candle(x.open, x.high, x.low, x.close, x.volume) for x in request.candles],
            initial_capital=request.initial_capital,
            risk_fraction=request.risk_fraction,
            fee_bps=request.fee_bps,
            slippage_bps=request.slippage_bps,
        )
        return result.__dict__
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
