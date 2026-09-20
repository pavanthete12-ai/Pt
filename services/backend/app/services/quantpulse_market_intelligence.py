"""Provider-backed derivatives and volatility intelligence for QuantPulse.

This module never fabricates market-intelligence values. Missing provider data is
represented explicitly so downstream signal logic can avoid false precision.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
import os
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class MarketIntelligenceSnapshot:
    instrument_key: str
    as_of: str | None
    pcr: float | None
    total_put_oi: float | None
    total_call_oi: float | None
    put_change_oi: float | None
    call_change_oi: float | None
    max_pain: float | None
    spot_price: float | None
    india_vix: float | None
    derivatives_bias: float | None
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
            headers={"Accept": "application/json", "Authorization": f"Bearer {self.access_token}"},
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

    @staticmethod
    def _number(data: dict[str, Any], *names: str) -> float | None:
        for name in names:
            try:
                value = data.get(name)
                if value is not None:
                    return float(value)
            except (TypeError, ValueError):
                continue
        return None

    def _pcr(self, instrument_key: str, expiry: str, as_of: str) -> float | None:
        data = self._data(self._get(self.base_url, "/market/pcr", {
            "instrument_key": instrument_key, "expiry": expiry, "date": as_of, "bucket_interval": 60,
        }))
        value = self._number(data, "pcr")
        if value is None and isinstance(data.get("insights"), list) and data["insights"]:
            value = self._number(data["insights"][-1], "pcr")
        return value

    def _oi(self, instrument_key: str, expiry: str, as_of: str) -> tuple[float | None, float | None, float | None]:
        data = self._data(self._get(self.base_url, "/market/oi", {
            "instrument_key": instrument_key, "expiry": expiry, "date": as_of,
        }))
        return (
            self._number(data, "total_puts"),
            self._number(data, "total_calls"),
            self._number(data, "spot_closing_price"),
        )

    def _change_oi(self, instrument_key: str, expiry: str, as_of: str, interval: int = 1) -> tuple[float | None, float | None]:
        data = self._data(self._get(self.base_url, "/market/change-oi", {
            "instrument_key": instrument_key, "expiry": expiry, "date": as_of, "interval": interval,
        }))
        return (
            self._number(data, "total_put_change_oi"),
            self._number(data, "total_call_change_oi"),
        )

    def _max_pain(self, instrument_key: str, expiry: str, as_of: str) -> float | None:
        data = self._data(self._get(self.base_url, "/market/max-pain", {
            "instrument_key": instrument_key, "expiry": expiry, "date": as_of, "bucket_interval": 60,
        }))
        value = self._number(data, "max_pain", "max_pain_strike", "strike_price")
        if value is not None:
            return value
        insights = data.get("insights")
        if isinstance(insights, list):
            for item in reversed(insights):
                if isinstance(item, dict):
                    value = self._number(item, "max_pain", "max_pain_strike", "strike_price")
                    if value is not None:
                        return value
        return None

    def _india_vix(self) -> float | None:
        payload = self._get(self.quote_url, "/market-quote/ltp", {"instrument_key": "NSE_INDEX|India VIX"})
        data = payload.get("data")
        if not isinstance(data, dict):
            return None
        for item in data.values():
            if isinstance(item, dict):
                value = self._number(item, "last_price", "ltp")
                if value is not None:
                    return value
        return None

    @staticmethod
    def _bias(
        pcr: float | None,
        put_change: float | None,
        call_change: float | None,
        spot: float | None,
        max_pain: float | None,
    ) -> float | None:
        components: list[float] = []
        if pcr is not None:
            # PCR above 1 is not intrinsically bullish; keep this component modest.
            components.append(max(-1.0, min(1.0, (pcr - 1.0) / 0.75)) * 0.45)
        if put_change is not None and call_change is not None:
            total = abs(put_change) + abs(call_change)
            if total > 0:
                components.append(max(-1.0, min(1.0, (put_change - call_change) / total)) * 0.35)
        if spot is not None and max_pain is not None and max_pain > 0:
            components.append(max(-1.0, min(1.0, (spot - max_pain) / max(spot, 1e-9) * 20)) * 0.20)
        return round(sum(components), 4) if components else None

    def snapshot(self, instrument_key: str, expiry: str = "current_week", as_of: str | None = None) -> MarketIntelligenceSnapshot:
        day = as_of or date.today().isoformat()
        notes: list[str] = []
        pcr = put_oi = call_oi = put_change = call_change = spot = max_pain = vix = None

        loaders = (
            ("PCR", lambda: self._pcr(instrument_key, expiry, day)),
            ("OI", lambda: self._oi(instrument_key, expiry, day)),
            ("Change OI", lambda: self._change_oi(instrument_key, expiry, day)),
            ("Max Pain", lambda: self._max_pain(instrument_key, expiry, day)),
            ("India VIX", self._india_vix),
        )
        for label, loader in loaders:
            try:
                value = loader()
                if label == "PCR":
                    pcr = value
                elif label == "OI":
                    put_oi, call_oi, spot = value
                elif label == "Change OI":
                    put_change, call_change = value
                elif label == "Max Pain":
                    max_pain = value
                else:
                    vix = value
            except Exception:
                notes.append(f"{label} unavailable")

        values = (pcr, put_oi, call_oi, put_change, call_change, max_pain, spot, vix)
        available = sum(v is not None for v in values)
        status = "provider-fed" if available >= 4 else "partial" if available else "unavailable"
        return MarketIntelligenceSnapshot(
            instrument_key=instrument_key, as_of=day, pcr=pcr,
            total_put_oi=put_oi, total_call_oi=call_oi,
            put_change_oi=put_change, call_change_oi=call_change,
            max_pain=max_pain, spot_price=spot, india_vix=vix,
            derivatives_bias=self._bias(pcr, put_change, call_change, spot, max_pain),
            status=status, source="upstox", notes=tuple(notes),
        )
