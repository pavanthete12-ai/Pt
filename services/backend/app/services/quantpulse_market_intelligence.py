"""Provider-backed derivatives and volatility intelligence for QuantPulse.

This module never fabricates market-intelligence values. Missing provider data is
represented explicitly so downstream signal logic can avoid false precision.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import os
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json


@dataclass(frozen=True)
class MarketIntelligenceSnapshot:
    instrument_key: str
    as_of: str | None
    pcr: float | None
    total_put_oi: float | None
    total_call_oi: float | None
    max_pain: float | None
    spot_price: float | None
    india_vix: float | None
    status: str
    source: str
    notes: tuple[str, ...] = ()


class UpstoxMarketIntelligenceProvider:
    """Small stdlib-only adapter for Upstox market-information APIs."""

    base_url = "https://api.upstox.com/v2"
    quote_url = "https://api.upstox.com/v3"

    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token or os.getenv("UPSTOX_ACCESS_TOKEN")

    def _get(self, base: str, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.access_token:
            raise RuntimeError("Upstox access token is not configured")
        query = urlencode({k: v for k, v in params.items() if v is not None})
        request = Request(
            f"{base}{path}?{query}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}",
            },
        )
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError("Unexpected provider response")
        return payload

    @staticmethod
    def _data(payload: dict[str, Any]) -> dict[str, Any]:
        data = payload.get("data")
        return data if isinstance(data, dict) else {}

    def _pcr(self, instrument_key: str, expiry: str, as_of: str) -> float | None:
        data = self._data(
            self._get(
                self.base_url,
                "/market/pcr",
                {
                    "instrument_key": instrument_key,
                    "expiry": expiry,
                    "date": as_of,
                    "bucket_interval": 60,
                },
            )
        )
        value = data.get("pcr")
        if value is None and isinstance(data.get("insights"), list) and data["insights"]:
            value = data["insights"][-1].get("pcr")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _oi(self, instrument_key: str, expiry: str, as_of: str) -> tuple[float | None, float | None, float | None]:
        data = self._data(
            self._get(
                self.base_url,
                "/market/oi",
                {"instrument_key": instrument_key, "expiry": expiry, "date": as_of},
            )
        )
        def number(name: str) -> float | None:
            try:
                value = data.get(name)
                return float(value) if value is not None else None
            except (TypeError, ValueError):
                return None
        return number("total_puts"), number("total_calls"), number("spot_closing_price")

    def _max_pain(self, instrument_key: str, expiry: str, as_of: str) -> float | None:
        data = self._data(
            self._get(
                self.base_url,
                "/market/max-pain",
                {
                    "instrument_key": instrument_key,
                    "expiry": expiry,
                    "date": as_of,
                    "bucket_interval": 60,
                },
            )
        )
        for key in ("max_pain", "max_pain_strike", "strike_price"):
            try:
                value = data.get(key)
                if value is not None:
                    return float(value)
            except (TypeError, ValueError):
                pass
        insights = data.get("insights")
        if isinstance(insights, list) and insights:
            for item in reversed(insights):
                if isinstance(item, dict):
                    for key in ("max_pain", "max_pain_strike", "strike_price"):
                        try:
                            value = item.get(key)
                            if value is not None:
                                return float(value)
                        except (TypeError, ValueError):
                            pass
        return None

    def _india_vix(self) -> float | None:
        payload = self._get(
            self.quote_url,
            "/market-quote/ltp",
            {"instrument_key": "NSE_INDEX|India VIX"},
        )
        data = payload.get("data")
        if not isinstance(data, dict):
            return None
        # Upstox keys can be normalized or instrument-key based.
        for item in data.values():
            if isinstance(item, dict):
                for key in ("last_price", "ltp"):
                    try:
                        value = item.get(key)
                        if value is not None:
                            return float(value)
                    except (TypeError, ValueError):
                        pass
        return None

    def snapshot(
        self,
        instrument_key: str,
        expiry: str = "current_week",
        as_of: str | None = None,
    ) -> MarketIntelligenceSnapshot:
        day = as_of or date.today().isoformat()
        notes: list[str] = []
        pcr = put_oi = call_oi = spot = max_pain = vix = None

        for label, loader in (
            ("PCR", lambda: self._pcr(instrument_key, expiry, day)),
            ("OI", lambda: self._oi(instrument_key, expiry, day)),
            ("Max Pain", lambda: self._max_pain(instrument_key, expiry, day)),
            ("India VIX", self._india_vix),
        ):
            try:
                value = loader()
                if label == "PCR":
                    pcr = value
                elif label == "OI":
                    put_oi, call_oi, spot = value
                elif label == "Max Pain":
                    max_pain = value
                else:
                    vix = value
            except Exception:
                notes.append(f"{label} unavailable")

        available = sum(v is not None for v in (pcr, put_oi, call_oi, max_pain, spot, vix))
        status = "provider-fed" if available >= 3 else "partial" if available else "unavailable"
        return MarketIntelligenceSnapshot(
            instrument_key=instrument_key,
            as_of=day,
            pcr=pcr,
            total_put_oi=put_oi,
            total_call_oi=call_oi,
            max_pain=max_pain,
            spot_price=spot,
            india_vix=vix,
            status=status,
            source="upstox",
            notes=tuple(notes),
        )
