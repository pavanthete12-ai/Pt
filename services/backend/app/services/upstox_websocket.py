"""Official Upstox V3 WebSocket market adapter.

The adapter uses the official Python SDK's MarketDataStreamerV3. Provider callbacks
are bridged into the asyncio event loop and only validated provider OHLC data is
published. It does not synthesize ticks or candles.
"""
from __future__ import annotations
import asyncio
import os
from datetime import datetime, timezone
from typing import Any
from app.api.routes.quantpulse_stream import publish_candle
from app.services.quantpulse_market import OHLCV

class UpstoxWebsocketFeed:
    def __init__(self) -> None:
        self.access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
        self.symbols = self._parse_symbols(os.getenv("QUANTPULSE_UPSTOX_SYMBOLS", ""))
        self.mode = os.getenv("QUANTPULSE_UPSTOX_MODE", "full")
        self.loop: asyncio.AbstractEventLoop | None = None
        self.streamer: Any = None
        self._started = False

    @staticmethod
    def _parse_symbols(value: str) -> dict[str, str]:
        result = {}
        for item in value.split(","):
            if "=" not in item:
                continue
            symbol, instrument = item.split("=", 1)
            if symbol.strip() and instrument.strip():
                result[symbol.strip().upper()] = instrument.strip()
        return result

    async def start(self) -> None:
        if self._started or not self.access_token or not self.symbols:
            return
        self.loop = asyncio.get_running_loop()
        try:
            import upstox_client
        except ImportError:
            return
        configuration = upstox_client.Configuration()
        configuration.access_token = self.access_token
        self.streamer = upstox_client.MarketDataStreamerV3(
            upstox_client.ApiClient(configuration),
            list(self.symbols.values()),
            self.mode,
        )
        self.streamer.on("open", self._on_open)
        self.streamer.on("message", self._on_message)
        self.streamer.on("error", self._on_error)
        self.streamer.on("close", self._on_close)
        self.streamer.auto_reconnect(True, 5, 10)
        self._connect_task = asyncio.create_task(asyncio.to_thread(self.streamer.connect), name="quantpulse-upstox-ws-connect")
        self._started = True

    async def stop(self) -> None:
        if self.streamer:
            try:
                await asyncio.to_thread(self.streamer.disconnect)
            except Exception:
                pass
        connect_task = getattr(self, "_connect_task", None)
        if connect_task and not connect_task.done():
            connect_task.cancel()
        self.streamer = None
        self._started = False

    def _on_open(self) -> None:
        if self.streamer and self.symbols:
            self.streamer.subscribe(list(self.symbols.values()), self.mode)

    def _on_message(self, message: Any) -> None:
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._handle_message(message), self.loop)

    async def _handle_message(self, message: Any) -> None:
        # SDK versions may expose a decoded model or raw bytes. We accept decoded
        # dictionaries/models here and deliberately ignore unknown formats.
        data = message
        if isinstance(data, bytes):
            return
        if hasattr(data, "to_dict"):
            data = data.to_dict()
        if not isinstance(data, dict):
            return
        feeds = data.get("feeds") or {}
        current_ts = data.get("currentTs") or data.get("current_ts")
        for instrument, feed in feeds.items():
            mapping = next((s for s, i in self.symbols.items() if i == instrument), None)
            if not mapping:
                continue
            ohlc_items = (((feed.get("fullFeed") or feed.get("full_feed") or {}).get("marketOHLC") or {}).get("ohlc") or [])
            for item in ohlc_items:
                if item.get("interval") not in ("I1", "1m"):
                    continue
                try:
                    ts = int(item.get("ts") or current_ts)
                    if ts > 10_000_000_000:
                        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                    else:
                        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    candle = OHLCV(mapping, dt, float(item["open"]), float(item["high"]), float(item["low"]), float(item["close"]), float(item.get("vol", item.get("volume", 0))))
                    await publish_candle(candle)
                except (KeyError, TypeError, ValueError):
                    continue

    def _on_error(self, *_args: Any) -> None:
        return None

    def _on_close(self, *_args: Any) -> None:
        return None
