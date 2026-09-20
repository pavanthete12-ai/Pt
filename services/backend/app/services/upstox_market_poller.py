"""Upstox V3 market-data poller.

Uses the official V3 intraday candle endpoint as a provider-fed fallback. It only
runs when an access token and symbol map are configured, and never fabricates data.
"""
from __future__ import annotations
import asyncio
import os
from datetime import datetime
import httpx
from app.api.routes.quantpulse_stream import publish_candle
from app.services.quantpulse_market import OHLCV, validate_candles

class UpstoxMarketPoller:
    def __init__(self) -> None:
        self.access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
        self.symbols = self._parse_symbols(os.getenv("QUANTPULSE_UPSTOX_SYMBOLS", ""))
        self.interval = max(5, int(os.getenv("QUANTPULSE_UPSTOX_INTERVAL_SECONDS", "15")))
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._seen: dict[str, datetime] = {}

    @staticmethod
    def _parse_symbols(value: str) -> dict[str, str]:
        result = {}
        for item in value.split(","):
            if "=" not in item:
                continue
            symbol, instrument = item.split("=", 1)
            symbol, instrument = symbol.strip().upper(), instrument.strip()
            if symbol and instrument:
                result[symbol] = instrument
        return result

    async def start(self) -> None:
        if not self.access_token or not self.symbols:
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run(), name="quantpulse-upstox-market")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            await self._task
            self._task = None

    async def _run(self) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            while not self._stop.is_set():
                for symbol, instrument in self.symbols.items():
                    try:
                        await self._poll_symbol(client, symbol, instrument)
                    except Exception:
                        # Provider outages must not create synthetic market data.
                        continue
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=self.interval)
                except asyncio.TimeoutError:
                    pass

    async def _poll_symbol(self, client: httpx.AsyncClient, symbol: str, instrument: str) -> None:
        url = f"https://api.upstox.com/v3/historical-candle/intraday/{instrument}/minutes/1"
        response = await client.get(url, headers={"Authorization": f"Bearer {self.access_token}", "Accept": "application/json"})
        response.raise_for_status()
        rows = response.json().get("data", {}).get("candles", [])
        candles: list[OHLCV] = []
        for row in rows:
            if len(row) < 6:
                continue
            candles.append(OHLCV(symbol, datetime.fromisoformat(str(row[0]).replace("Z", "+00:00")), float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])))
        candles = validate_candles(sorted(candles, key=lambda c: c.timestamp))
        for candle in candles:
            if self._seen.get(symbol) and candle.timestamp <= self._seen[symbol]:
                continue
            await publish_candle(candle)
            self._seen[symbol] = candle.timestamp
