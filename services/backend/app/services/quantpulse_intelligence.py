"""Unified, cached external intelligence for QuantPulse.

External provider calls are cached briefly so a 1-minute candle stream does not
turn into one HTTP request per candle. Missing inputs stay explicit.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

from app.services.quantpulse_market_intelligence import UpstoxMarketIntelligenceProvider
from app.services.quantpulse_news import UpstoxNewsProvider


class QuantPulseIntelligenceService:
    def __init__(self, market_ttl: float = 30.0, news_ttl: float = 60.0) -> None:
        self.market_provider = UpstoxMarketIntelligenceProvider()
        self.news_provider = UpstoxNewsProvider()
        self.market_ttl = market_ttl
        self.news_ttl = news_ttl
        self._market_cache: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}
        self._news_cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def snapshot(
        self,
        instrument_key: str,
        expiry: str = "current_week",
        include_news: bool = True,
    ) -> dict[str, Any]:
        now = time.monotonic()
        market_key = (instrument_key, expiry)

        async with self._lock:
            cached_market = self._market_cache.get(market_key)
            cached_news = self._news_cache.get(instrument_key) if include_news else None

        if cached_market and now - cached_market[0] < self.market_ttl:
            market = cached_market[1]
        else:
            try:
                value = await asyncio.to_thread(
                    self.market_provider.snapshot,
                    instrument_key,
                    expiry,
                    None,
                )
                market = {
                    "instrument_key": value.instrument_key,
                    "as_of": value.as_of,
                    "pcr": value.pcr,
                    "total_put_oi": value.total_put_oi,
                    "total_call_oi": value.total_call_oi,
                    "put_change_oi": value.put_change_oi,
                    "call_change_oi": value.call_change_oi,
                    "max_pain": value.max_pain,
                    "spot_price": value.spot_price,
                    "india_vix": value.india_vix,
                    "derivatives_bias": value.derivatives_bias,
                    "status": value.status,
                    "source": value.source,
                    "notes": list(value.notes),
                }
            except Exception:
                market = {
                    "instrument_key": instrument_key,
                    "status": "unavailable",
                    "source": "upstox",
                    "notes": ["provider request failed"],
                }
            async with self._lock:
                self._market_cache[market_key] = (time.monotonic(), market)

        news: dict[str, Any]
        if not include_news:
            news = {"status": "disabled", "sentiment": 0.0, "impact": 0.0, "article_count": 0, "items": []}
        elif cached_news and now - cached_news[0] < self.news_ttl:
            news = cached_news[1]
        else:
            try:
                news = await self.news_provider.analyze(instrument_key, page_size=20)
            except Exception:
                news = {
                    "status": "unavailable",
                    "sentiment": 0.0,
                    "impact": 0.0,
                    "article_count": 0,
                    "items": [],
                }
            async with self._lock:
                self._news_cache[instrument_key] = (time.monotonic(), news)

        available = sum(
            market.get(k) is not None
            for k in ("pcr", "total_put_oi", "total_call_oi", "put_change_oi", "call_change_oi", "max_pain", "india_vix")
        )
        status = "ready" if market.get("status") == "provider-fed" and news.get("status") == "provider-fed" else "partial"
        return {
            "status": status,
            "market": market,
            "news": news,
            "quality": {
                "derivatives_fields_available": available,
                "news_available": news.get("status") == "provider-fed",
                "cache": {"market_ttl_seconds": self.market_ttl, "news_ttl_seconds": self.news_ttl},
            },
        }


_service = QuantPulseIntelligenceService()


def get_intelligence_service() -> QuantPulseIntelligenceService:
    return _service
