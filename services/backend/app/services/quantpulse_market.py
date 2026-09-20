"""Market-data normalization primitives for QuantPulse."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

@dataclass(frozen=True)
class OHLCV:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def validate(self) -> "OHLCV":
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("Invalid OHLC candle")
        if self.low < 0 or min(self.open, self.high, self.low, self.close) < 0:
            raise ValueError("Negative prices are not supported")
        return self

@dataclass
class MarketSnapshot:
    symbol: str
    price: float
    change: float
    change_pct: float
    timestamp: datetime
    source: str
    data_quality: str

class MarketDataAdapter:
    name = "abstract"
    async def snapshot(self, symbol: str) -> MarketSnapshot:
        raise NotImplementedError
    async def candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[OHLCV]:
        raise NotImplementedError

def normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

def validate_candles(candles: Iterable[OHLCV]) -> list[OHLCV]:
    normalized, previous = [], None
    for candle in candles:
        candle = OHLCV(candle.symbol.upper(), normalize_timestamp(candle.timestamp),
                       float(candle.open), float(candle.high), float(candle.low),
                       float(candle.close), float(candle.volume)).validate()
        if previous and candle.timestamp <= previous:
            raise ValueError("Candles must be strictly chronological")
        previous = candle.timestamp
        normalized.append(candle)
    return normalized
