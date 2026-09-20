from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from collections import defaultdict
from app.services.quantpulse_engine import Candle, analyze

TIMEFRAME_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "1D": 1440}

@dataclass
class _Bucket:
    start: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class MultiTimeframeAnalyzer:
    """Aggregates completed 1m candles and produces independent timeframe signals."""
    def __init__(self, max_candles: int = 250) -> None:
        self.max_candles = max_candles
        self._candles: dict[str, dict[str, list[Candle]]] = defaultdict(lambda: defaultdict(list))
        self._last_bucket: dict[tuple[str, str], datetime] = {}

    @staticmethod
    def _bucket(ts: datetime, minutes: int) -> datetime:
        ts = ts.astimezone(timezone.utc).replace(second=0, microsecond=0)
        total = ts.hour * 60 + ts.minute
        floored = (total // minutes) * minutes
        return ts.replace(hour=floored // 60, minute=floored % 60)

    def update(self, symbol: str, candle: Candle, timestamp: datetime) -> dict[str, dict] | None:
        output: dict[str, dict] = {}
        for timeframe, minutes in TIMEFRAME_MINUTES.items():
            if timeframe != "1m" and minutes > 1:
                bucket = self._bucket(timestamp, minutes)
                key = (symbol, timeframe)
                current = self._last_bucket.get(key)
                if current is not None and bucket == current:
                    continue
                self._last_bucket[key] = bucket
                if self._candles[symbol][timeframe]:
                    result = analyze(self._candles[symbol][timeframe])
                    output[timeframe] = result
                self._candles[symbol][timeframe].append(candle)
                if len(self._candles[symbol][timeframe]) > self.max_candles:
                    self._candles[symbol][timeframe].pop(0)
            else:
                self._candles[symbol][timeframe].append(candle)
                if len(self._candles[symbol][timeframe]) > self.max_candles:
                    self._candles[symbol][timeframe].pop(0)
                if len(self._candles[symbol][timeframe]) >= 20:
                    output[timeframe] = analyze(self._candles[symbol][timeframe])
        return output or None

def fuse_timeframes(analyses: dict[str, dict]) -> dict:
    weights = {"1m": 0.10, "5m": 0.20, "15m": 0.30, "1h": 0.25, "1D": 0.15}
    available = [(tf, analyses[tf]) for tf in weights if tf in analyses and analyses[tf].get("data_quality") == "OK"]
    if not available:
        return {"signal": "HOLD", "confidence": 0.0, "agreement": 0.0, "timeframes": {}}
    score = 0.0
    weight_total = 0.0
    for tf, result in available:
        direction = 1 if result["signal"] == "BUY" else -1 if result["signal"] == "SELL" else 0
        score += direction * weights[tf]
        weight_total += weights[tf]
    normalized = score / weight_total
    signal = "BUY" if normalized >= 0.35 else "SELL" if normalized <= -0.35 else "HOLD"
    agreement = round(abs(normalized) * 100, 1)
    return {
        "signal": signal,
        "confidence": agreement,
        "agreement": agreement,
        "timeframes": {tf: {"signal": r["signal"], "confidence": r["confidence"], "trend": r["trend"]} for tf, r in available},
        "disclaimer": "Multi-timeframe model strength, not a probability of profit.",
    }
