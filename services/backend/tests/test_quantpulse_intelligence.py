import pytest

from app.services.quantpulse_intelligence import QuantPulseIntelligenceService


@pytest.mark.asyncio
async def test_intelligence_snapshot_uses_cache(monkeypatch):
    service = QuantPulseIntelligenceService(market_ttl=60, news_ttl=60)
    calls = {"market": 0, "news": 0}

    class Market:
        def snapshot(self, *args):
            calls["market"] += 1
            return type("S", (), {
                "instrument_key": args[0], "as_of": "2026-09-21",
                "pcr": 1.1, "total_put_oi": 100.0, "total_call_oi": 90.0,
                "put_change_oi": 10.0, "call_change_oi": -5.0, "max_pain": 25000.0,
                "spot_price": 25100.0, "india_vix": 14.0, "derivatives_bias": 0.2,
                "status": "provider-fed", "source": "upstox", "notes": (),
            })()

    class News:
        async def analyze(self, *args, **kwargs):
            calls["news"] += 1
            return {"status": "provider-fed", "sentiment": 0.2, "impact": 0.3, "article_count": 1, "items": []}

    service.market_provider = Market()
    service.news_provider = News()

    first = await service.snapshot("NSE_INDEX|Nifty 50")
    second = await service.snapshot("NSE_INDEX|Nifty 50")

    assert first["status"] == "ready"
    assert second["status"] == "ready"
    assert calls == {"market": 1, "news": 1}


@pytest.mark.asyncio
async def test_intelligence_keeps_provider_failure_explicit():
    service = QuantPulseIntelligenceService()
    service.market_provider = type("Market", (), {
        "snapshot": lambda *args: (_ for _ in ()).throw(RuntimeError("down"))
    })()
    service.news_provider = type("News", (), {
        "analyze": lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("down"))
    })()

    result = await service.snapshot("NSE_INDEX|Nifty 50")
    assert result["status"] == "partial"
    assert result["market"]["status"] == "unavailable"
    assert result["news"]["status"] == "unavailable"
