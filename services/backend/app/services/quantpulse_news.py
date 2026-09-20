"""Upstox-backed market news intelligence.

The provider is optional. If credentials or an instrument mapping are missing,
the service returns an explicit unavailable state rather than fabricated news.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx


@dataclass(frozen=True)
class NewsItem:
    headline: str
    summary: str
    url: str
    published_at: datetime
    sentiment: float
    relevance: float


_POSITIVE = {
    "beat", "beats", "growth", "surge", "surges", "gain", "gains", "upgrade",
    "profit", "profits", "record", "strong", "stronger", "positive", "rally",
    "rises", "rise", "outperform", "approval", "approved", "expansion",
}
_NEGATIVE = {
    "miss", "misses", "fall", "falls", "drop", "drops", "downgrade", "loss",
    "losses", "weak", "weaker", "negative", "decline", "declines", "cut",
    "cuts", "warning", "probe", "investigation", "lawsuit", "default",
}


def _sentiment(text: str) -> float:
    words = set(re.findall(r"[a-z]+", text.lower()))
    pos = len(words & _POSITIVE)
    neg = len(words & _NEGATIVE)
    if pos == neg == 0:
        return 0.0
    return round(max(-1.0, min(1.0, (pos - neg) / max(3, pos + neg))), 3)


class UpstoxNewsProvider:
    base_url = "https://api.upstox.com/v2"

    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token or os.getenv("UPSTOX_ACCESS_TOKEN")

    def _headers(self) -> dict[str, str]:
        if not self.access_token:
            raise RuntimeError("UPSTOX_ACCESS_TOKEN is not configured")
        return {"Authorization": f"Bearer {self.access_token}", "Accept": "application/json"}

    async def fetch(self, instrument_key: str, page_size: int = 20) -> list[NewsItem]:
        if not instrument_key:
            return []
        params = {
            "category": "instrument_keys",
            "instrument_keys": instrument_key,
            "page_number": 1,
            "page_size": max(1, min(page_size, 100)),
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self.base_url}/news", params=params, headers=self._headers())
            response.raise_for_status()
            body = response.json()

        raw_items = body.get("data", {}).get(instrument_key, [])
        items: list[NewsItem] = []
        for item in raw_items:
            timestamp = item.get("published_timestamp") or item.get("published_at")
            if timestamp is None:
                continue
            try:
                if isinstance(timestamp, (int, float)):
                    published = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                else:
                    published = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
                    if published.tzinfo is None:
                        published = published.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError, OverflowError):
                continue

            headline = str(item.get("heading") or item.get("headline") or "").strip()
            summary = str(item.get("summary") or "").strip()
            if not headline:
                continue
            items.append(
                NewsItem(
                    headline=headline,
                    summary=summary,
                    url=str(item.get("url") or item.get("article_url") or ""),
                    published_at=published.astimezone(timezone.utc),
                    sentiment=_sentiment(f"{headline} {summary}"),
                    relevance=1.0,
                )
            )
        return items

    async def analyze(self, instrument_key: str, page_size: int = 20) -> dict:
        items = await self.fetch(instrument_key, page_size)
        if not items:
            return {
                "status": "no_recent_news",
                "sentiment": 0.0,
                "impact": 0.0,
                "article_count": 0,
                "items": [],
            }

        weighted = sum(item.sentiment * item.relevance for item in items)
        weight = sum(item.relevance for item in items)
        sentiment = round(weighted / weight, 3) if weight else 0.0
        impact = round(min(1.0, abs(sentiment) * min(1.0, len(items) / 5)), 3)

        return {
            "status": "provider-fed",
            "sentiment": sentiment,
            "impact": impact,
            "article_count": len(items),
            "latest_published_at": max(item.published_at for item in items).isoformat(),
            "items": [
                {
                    "headline": item.headline,
                    "summary": item.summary,
                    "url": item.url,
                    "published_at": item.published_at.isoformat(),
                    "sentiment": item.sentiment,
                }
                for item in items[:10]
            ],
        }
