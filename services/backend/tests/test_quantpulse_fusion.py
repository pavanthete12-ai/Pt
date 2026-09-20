import pytest

from app.services.quantpulse_engine import Candle
from app.services.quantpulse_fusion import fuse


@pytest.mark.asyncio
async def test_fusion_is_explainable_and_bounded(monkeypatch):
    class Intelligence:
        async def snapshot(self, *args, **kwargs):
            return {
                "status": "ready",
                "market": {
                    "derivatives_bias": 0.4,
                    "india_vix": 14.0,
                    "status": "provider-fed",
                },
                "news": {
                    "status": "provider-fed",
                    "sentiment": 0.2,
                    "impact": 0.2,
                },
                "quality": {},
            }

    import app.services.quantpulse_fusion as module
    monkeypatch.setattr(module, "get_intelligence_service", lambda: Intelligence())

    candles = [
        Candle(100 + i, 102 + i, 99 + i, 101 + i, 1000)
        for i in range(40)
    ]
    result = await fuse(candles, "NSE_INDEX|Nifty 50")

    assert result["signal"] in {"BUY", "SELL", "HOLD"}
    assert 0 <= result["confidence"] <= 99
    assert -1 <= result["model_score"] <= 1
    assert result["status"] == "experimental-fusion"
    assert set(result["factor_contributions"]) == {"technical", "news", "derivatives", "volatility"}
