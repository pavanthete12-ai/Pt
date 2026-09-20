"""Deterministic QuantPulse signal engine.

Produces an explainable analytical signal from OHLCV data. It never fabricates
news or market data and does not represent confidence as profit probability.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Literal

Signal = Literal["BUY", "SELL", "HOLD"]


@dataclass(frozen=True)
class Candle:
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


def _ema(values: list[float], period: int) -> float:
    if not values:
        return 0.0
    alpha = 2 / (period + 1)
    value = values[0]
    for item in values[1:]:
        value = alpha * item + (1 - alpha) * value
    return value


def _rsi(values: list[float], period: int = 14) -> float:
    if len(values) < 2:
        return 50.0
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    recent = changes[-period:]
    gains = [max(x, 0.0) for x in recent]
    losses = [max(-x, 0.0) for x in recent]
    avg_gain = mean(gains) if gains else 0.0
    avg_loss = mean(losses) if losses else 0.0
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _atr(candles: list[Candle], period: int = 14) -> float:
    if len(candles) < 2:
        return 0.0
    trs: list[float] = []
    for i in range(1, len(candles)):
        current, previous = candles[i], candles[i - 1]
        trs.append(
            max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            )
        )
    return mean(trs[-period:]) if trs else 0.0


def _pattern(c: Candle) -> str:
    body = abs(c.close - c.open)
    span = max(c.high - c.low, 1e-9)
    upper = c.high - max(c.open, c.close)
    lower = min(c.open, c.close) - c.low
    if body / span < 0.12:
        return "Doji"
    if lower > body * 2 and upper < body:
        return "Bullish hammer"
    if upper > body * 2 and lower < body:
        return "Bearish rejection"
    if c.close > c.open and body / span > 0.65:
        return "Bullish impulse"
    if c.close < c.open and body / span > 0.65:
        return "Bearish impulse"
    return "Neutral candle"


def _volume_regime(candles: list[Candle], lookback: int = 20) -> tuple[float, str]:
    volumes = [max(0.0, c.volume) for c in candles[-lookback:]]
    if len(volumes) < 5 or mean(volumes) <= 0:
        return 0.0, "Unavailable"
    baseline = mean(volumes[:-1]) if len(volumes) > 1 else volumes[0]
    if baseline <= 0:
        return 0.0, "Unavailable"
    ratio = volumes[-1] / baseline
    if ratio >= 1.5:
        return min(1.0, (ratio - 1.0) / 2.0), "Expansion"
    if ratio <= 0.65:
        return -0.25, "Compression"
    return 0.0, "Normal"


def _structure_score(candles: list[Candle], lookback: int = 20) -> tuple[float, str]:
    recent = candles[-lookback:]
    if len(recent) < 6:
        return 0.0, "Insufficient history"
    highs = [c.high for c in recent]
    lows = [c.low for c in recent]
    last = recent[-1]
    prior_high = max(highs[:-1])
    prior_low = min(lows[:-1])
    if last.close > prior_high:
        return 1.0, "Upside breakout"
    if last.close < prior_low:
        return -1.0, "Downside breakdown"
    midpoint = (prior_high + prior_low) / 2
    distance = (last.close - midpoint) / max(prior_high - prior_low, 1e-9)
    if distance > 0.25:
        return 0.35, "Upper-range structure"
    if distance < -0.25:
        return -0.35, "Lower-range structure"
    return 0.0, "Range"


def analyze(candles: list[Candle], news_sentiment: float = 0.0) -> dict:
    if len(candles) < 20:
        raise ValueError("At least 20 candles are required")

    closes = [c.close for c in candles]
    last = candles[-1]
    ema9, ema21 = _ema(closes, 9), _ema(closes, 21)
    rsi = _rsi(closes)
    atr = _atr(candles)
    trend = 1.0 if ema9 > ema21 else -1.0
    momentum = max(-1.0, min(1.0, (rsi - 50) / 25))
    pattern_name = _pattern(last)
    pattern = (
        1.0 if "Bullish" in pattern_name
        else -1.0 if "Bearish" in pattern_name
        else 0.0
    )
    structure, structure_label = _structure_score(candles)
    volume, volume_regime = _volume_regime(candles)
    news = max(-1.0, min(1.0, news_sentiment))

    # Technical structure carries most of the score. News is optional and
    # remains neutral until a validated provider supplies a timestamped signal.
    score = (
        0.30 * trend
        + 0.20 * momentum
        + 0.15 * pattern
        + 0.20 * structure
        + 0.10 * volume
        + 0.05 * news
    )
    signal: Signal = "BUY" if score >= 0.25 else "SELL" if score <= -0.25 else "HOLD"

    confidence = round(min(99.0, 50.0 + abs(score) * 45.0), 1)
    if trend > 0 and momentum >= 0 and structure >= 0:
        regime = "Bullish"
    elif trend < 0 and momentum <= 0 and structure <= 0:
        regime = "Bearish"
    else:
        regime = "Mixed"

    stop_distance = max(atr * 1.5, last.close * 0.003)
    if signal == "BUY":
        stop, target = last.close - stop_distance, last.close + stop_distance * 2
    elif signal == "SELL":
        stop, target = last.close + stop_distance, last.close - stop_distance * 2
    else:
        stop, target = last.close - stop_distance, last.close + stop_distance * 2

    return {
        "signal": signal,
        "confidence": confidence,
        "model_score": round(score, 4),
        "price": round(last.close, 2),
        "ema9": round(ema9, 2),
        "ema21": round(ema21, 2),
        "rsi": round(rsi, 2),
        "atr": round(atr, 2),
        "trend": "BULLISH" if trend > 0 else "BEARISH",
        "momentum": round(momentum, 3),
        "pattern": pattern_name,
        "structure": structure_label,
        "structure_score": round(structure, 3),
        "volume_regime": volume_regime,
        "volume_score": round(volume, 3),
        "news_sentiment": round(news, 3),
        "news_status": "provider-fed" if news != 0 else "neutral-no-provider",
        "market_regime": regime,
        "factor_contributions": {
            "trend": round(0.30 * trend, 4),
            "momentum": round(0.20 * momentum, 4),
            "pattern": round(0.15 * pattern, 4),
            "structure": round(0.20 * structure, 4),
            "volume": round(0.10 * volume, 4),
            "news": round(0.05 * news, 4),
        },
        "stop_loss": round(stop, 2),
        "target": round(target, 2),
        "risk_reward": 2.0,
        "data_quality": "OK",
        "disclaimer": "Analytical model strength; not a guaranteed return or probability of profit.",
    }
