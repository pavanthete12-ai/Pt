"""WebSocket market stream with validated candle broadcasting.

Provider integrations can call publish_candle() after validating their payload.
The endpoint never fabricates market prices.
"""

import asyncio
import json
from collections import defaultdict, deque
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.session import AsyncSessionLocal
from app.services.quantpulse_engine import Candle, analyze
from app.services.quantpulse_market import OHLCV, validate_candles
from app.services.quantpulse_mtf import MultiTimeframeAnalyzer, fuse_timeframes
from app.services.quantpulse_paper_manager import process_candle_for_paper_positions

router = APIRouter(prefix="/quantpulse/stream", tags=["quantpulse-stream"])

_clients: dict[WebSocket, set[tuple[str, str]]] = {}
_lock = asyncio.Lock()
_history: dict[str, deque[OHLCV]] = defaultdict(lambda: deque(maxlen=200))
_mtf = MultiTimeframeAnalyzer()


async def publish_candle(candle: OHLCV) -> None:
    normalized = validate_candles([candle])[0]

    async with _lock:
        history = _history[normalized.symbol]
        if history and normalized.timestamp <= history[-1].timestamp:
            return
        history.append(normalized)

        engine_candles = [
            Candle(c.open, c.high, c.low, c.close, c.volume) for c in history
        ]
        analysis = analyze(engine_candles) if len(history) >= 20 else None
        mtf = _mtf.update(
            normalized.symbol, engine_candles[-1], normalized.timestamp
        )
        fusion = fuse_timeframes(mtf) if mtf else None

        payload = {
            "type": "candle",
            "symbol": normalized.symbol,
            "timestamp": normalized.timestamp.isoformat(),
            "open": normalized.open,
            "high": normalized.high,
            "low": normalized.low,
            "close": normalized.close,
            "volume": normalized.volume,
        }
        if analysis is not None:
            payload["analysis"] = analysis
        if mtf:
            payload["timeframes"] = mtf
            payload["fusion"] = fusion

        recipients = [
            client
            for client, subscriptions in _clients.items()
            if (normalized.symbol, "1m") in subscriptions
            or any(
                symbol == normalized.symbol and timeframe in mtf
                for symbol, timeframe in subscriptions
            )
        ]

    async with AsyncSessionLocal() as session:
        await process_candle_for_paper_positions(
            session,
            symbol=normalized.symbol,
            high=normalized.high,
            low=normalized.low,
            close=normalized.close,
        )

    dead: list[WebSocket] = []
    for client in recipients:
        try:
            await client.send_json(payload)
        except Exception:
            dead.append(client)

    if dead:
        async with _lock:
            for client in dead:
                _clients.pop(client, None)


@router.websocket("")
async def market_stream(websocket: WebSocket):
    await websocket.accept()
    async with _lock:
        _clients[websocket] = set()

    try:
        await websocket.send_json(
            {"type": "connected", "service": "QuantPulse", "mode": "provider-fed"}
        )

        while True:
            message = await websocket.receive_text()
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "message": "Expected JSON"}
                )
                continue

            message_type = payload.get("type")

            if message_type == "heartbeat":
                await websocket.send_json(
                    {"type": "heartbeat", "ts": payload.get("ts")}
                )
                continue

            if message_type == "subscribe":
                symbol = str(payload.get("symbol", "")).upper().strip()
                timeframe = str(payload.get("timeframe", "1m")).strip()

                if (
                    not symbol
                    or len(symbol) > 32
                    or timeframe not in {"1m", "5m", "15m", "1h", "1D"}
                ):
                    await websocket.send_json(
                        {"type": "error", "message": "Invalid symbol or timeframe"}
                    )
                    continue

                async with _lock:
                    _clients[websocket].add((symbol, timeframe))

                await websocket.send_json(
                    {
                        "type": "subscribed",
                        "symbol": symbol,
                        "timeframe": timeframe,
                    }
                )
                continue

            if message_type == "unsubscribe":
                symbol = str(payload.get("symbol", "")).upper().strip()
                timeframe = str(payload.get("timeframe", "1m")).strip()

                async with _lock:
                    subscriptions = _clients.get(websocket)
                    if subscriptions is not None:
                        subscriptions.discard((symbol, timeframe))

                await websocket.send_json(
                    {
                        "type": "unsubscribed",
                        "symbol": symbol,
                        "timeframe": timeframe,
                    }
                )
                continue

            await websocket.send_json(
                {"type": "error", "message": "Unsupported stream message"}
            )

    except WebSocketDisconnect:
        pass
    finally:
        async with _lock:
            _clients.pop(websocket, None)
