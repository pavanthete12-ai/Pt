"""Unified QuantPulse fusion layer.

This is an experimental, explainable score combining technical analysis with
timestamped provider intelligence. It must be validated in backtests before
being used for any live order routing.
"""
from __future__ import annotations

from app.services.quantpulse_engine import Candle, analyze
from app.services.quantpulse_intelligence import get_intelligence_service


def _clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _vix_component(vix: float | None) -> float:
    if vix is None:
        return 0.0
    # Volatility itself is not directional. Keep this factor small and only
    # penalize extreme volatility rather than treating high VIX as bearish.
    if vix <= 14:
        return 0.0
    if vix >= 30:
        return -0.20
    return -0.20 * ((vix - 14) / 16)


async def fuse(
    candles: list[Candle],
    instrument_key: str,
    expiry: str = "current_week",
) -> dict:
    technical = analyze(candles, news_sentiment=0.0)
    intelligence = await get_intelligence_service().snapshot(instrument_key, expiry)

    market = intelligence["market"]
    news = intelligence["news"]

    technical_score = float(technical["model_score"])
    news_score = _clamp(float(news.get("sentiment", 0.0))) if news.get("status") == "provider-fed" else 0.0
    derivatives_score = _clamp(float(market["derivatives_bias"])) if market.get("derivatives_bias") is not None else 0.0
    vix_score = _vix_component(market.get("india_vix"))

    # Technicals remain dominant. External factors are deliberately bounded.
    weights = {"technical": 0.70, "news": 0.10, "derivatives": 0.15, "volatility": 0.05}
    score = (
        technical_score * weights["technical"]
        + news_score * weights["news"]
        + derivatives_score * weights["derivatives"]
        + vix_score * weights["volatility"]
    )
    score = _clamp(score)

    signal = "BUY" if score >= 0.25 else "SELL" if score <= -0.25 else "HOLD"
    strength = round(min(99.0, 50.0 + abs(score) * 45.0), 1)

    return {
        "signal": signal,
        "confidence": strength,
        "model_score": round(score, 4),
        "technical": technical,
        "intelligence": intelligence,
        "factor_contributions": {
            "technical": round(technical_score * weights["technical"], 4),
            "news": round(news_score * weights["news"], 4),
            "derivatives": round(derivatives_score * weights["derivatives"], 4),
            "volatility": round(vix_score * weights["volatility"], 4),
        },
        "weights": weights,
        "status": "experimental-fusion",
        "disclaimer": (
            "Confidence is model strength, not probability of profit. "
            "External intelligence is provider-fed when available. "
            "This fusion layer requires out-of-sample validation before live execution."
        ),
    }
