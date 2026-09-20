from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

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

    def update(self, candle: Candle) -> None:
        self.high = max(self.high, candle.high)
        self.low = min(self.low, candle.low)
        self.close = candle.close
        self.volume += candle.volume

    def to_candle(self) -> Candle:
        return Candle(
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
        )


class MultiTimeframeAnalyzer:
    """Aggregate completed 1m candles into true OHLCV higher-timeframe candles."""

    def __init__(self, max_candles: int = 250) -> None:
        self.max_candles = max_candles
        self._candles: dict[str, dict[str, list[Candle]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._buckets: dict[tuple[str, str], _Bucket] = {}

    @staticmethod
    def _bucket(ts: datetime, minutes: int) -> datetime:
        ts = ts.astimezone(timezone.utc).replace(second=0, microsecond=0)
        total = ts.hour * 60 + ts.minute
        floored = (total // minutes) * minutes
        return ts.replace(hour=floored // 60, minute=floored % 60)

    def _append_completed(self, symbol: str, timeframe: str, candle: Candle) -> None:
        series = self._candles[symbol][timeframe]
        series.append(candle)
        if len(series) > self.max_candles:
            series.pop(0)

    def update(self, symbol: str, candle: Candle, timestamp: datetime) -> dict[str, dict] | None:
        output: dict[str, dict] = {}

        # 1m is already the base timeframe and can be analyzed immediately.
        series_1m = self._candles[symbol]["1m"]
        series_1m.append(candle)
        if len(series_1m) > self.max_candles:
            series_1m.pop(0)
        if len(series_1m) >= 20:
            output["1m"] = analyze(series_1m)

        # Higher timeframes are built from every incoming 1m candle.
        for timeframe, minutes in TIMEFRAME_MINUTES.items():
            if minutes == 1:
                continue

            key = (symbol, timeframe)
            bucket_start = self._bucket(timestamp, minutes)
            current = self._buckets.get(key)

            if current is None:
                self._buckets[key] = _Bucket(
                    start=bucket_start,
                    open=candle.open,
                    high=candle.high,
                    low=candle.low,
                    close=candle.close,
                    volume=candle.volume,
                )
                continue

            if bucket_start == current.start:
                current.update(candle)
                continue

            # The previous bucket is now complete. Only completed candles
            # participate in higher-timeframe analysis.
            self._append_completed(symbol, timeframe, current.to_candle())
            if len(self._candles[symbol][timeframe]) >= 20:
                output[timeframe] = analyze(self._candles[symbol][timeframe])

            self._buckets[key] = _Bucket(
                start=bucket_start,
                open=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=candle.volume,
            )

        return output or None


def fuse_timeframes(analyses: dict[str, dict]) -> dict:
    weights = {"1m": 0.10, "5m": 0.20, "15m": 0.30, "1h": 0.25, "1D": 0.15}
    available = [
        (tf, analyses[tf])
        for tf in weights
        if tf in analyses and analyses[tf].get("data_quality") == "OK"
    ]

    if not available:
        return {
            "signal": "HOLD",
            "confidence": 0.0,
            "agreement": 0.0,
            "timeframes": {},
            "disclaimer": "No validated timeframe analyses are available.",
        }

    score = 0.0
    weight_total = 0.0
    for tf, result in available:
        direction = (
            1 if result["signal"] == "BUY" else -1 if result["signal"] == "SELL" else 0
        )
        score += direction * weights[tf]
        weight_total += weights[tf]

    normalized = score / weight_total
    signal = "BUY" if normalized >= 0.35 else "SELL" if normalized <= -0.35 else "HOLD"
    agreement = round(abs(normalized) * 100, 1)

    return {
        "signal": signal,
        "confidence": agreement,
        "agreement": agreement,
        "timeframes": {
            tf: {
                "signal": r["signal"],
                "confidence": r["confidence"],
                "trend": r["trend"],
            }
            for tf, r in available
        },
        "disclaimer": "Multi-timeframe model strength, not a probability of profit.",
    }
