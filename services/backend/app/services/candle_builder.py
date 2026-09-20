"""Simple candle aggregation for provider ticks.

A production adapter can feed ticks into this service. Completed candles are
emitted to the QuantPulse WebSocket broadcaster.
"""
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class CandleBuilder:
    symbol: str
    timeframe_seconds: int
    bucket_start: int | None = None
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0

    def update(self, timestamp: datetime, price: float, volume: float = 0.0) -> dict | None:
        if price <= 0 or volume < 0:
            raise ValueError("Invalid tick")
        ts = int(timestamp.astimezone(timezone.utc).timestamp())
        bucket = ts - (ts % self.timeframe_seconds)
        completed = None
        if self.bucket_start is None:
            self.bucket_start = bucket
            self.open = self.high = self.low = self.close = price
            self.volume = volume
            return None
        if bucket != self.bucket_start:
            completed = {"symbol":self.symbol.upper(),"timestamp":datetime.fromtimestamp(self.bucket_start,tz=timezone.utc),"open":self.open,"high":self.high,"low":self.low,"close":self.close,"volume":self.volume}
            self.bucket_start = bucket
            self.open = self.high = self.low = self.close = price
            self.volume = volume
            return completed
        self.high = max(self.high, price)
        self.low = min(self.low, price)
        self.close = price
        self.volume += volume
        return None
