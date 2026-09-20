"""WebSocket market stream with validated candle broadcasting.

Provider integrations can call publish_candle() after validating their payload.
The endpoint never fabricates market prices.
"""
import asyncio
import json
from collections import defaultdict, deque
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.quantpulse_market import OHLCV, validate_candles
from app.services.quantpulse_engine import Candle, analyze

router = APIRouter(prefix="/quantpulse/stream", tags=["quantpulse-stream"])
_clients: set[WebSocket] = set()
_lock = asyncio.Lock()
_history: dict[str, deque[OHLCV]] = defaultdict(lambda: deque(maxlen=200))

async def publish_candle(candle: OHLCV) -> None:
    normalized = validate_candles([candle])[0]
    async with _lock:
        history = _history[normalized.symbol]
        if history and normalized.timestamp <= history[-1].timestamp:
            return
        history.append(normalized)
        analysis = analyze([Candle(c.open, c.high, c.low, c.close, c.volume) for c in history]) if len(history) >= 20 else None
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
    async with _lock:
        clients = list(_clients)
    dead: list[WebSocket] = []
    for client in clients:
        try:
            await client.send_json(payload)
        except Exception:
            dead.append(client)
    if dead:
        async with _lock:
            for client in dead:
                _clients.discard(client)

@router.websocket("")
async def market_stream(websocket: WebSocket):
    await websocket.accept()
    async with _lock:
        _clients.add(websocket)
    try:
        await websocket.send_json({"type":"connected","service":"QuantPulse","mode":"provider-fed"})
        while True:
            message = await websocket.receive_text()
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send_json({"type":"error","message":"Expected JSON"})
                continue
            if payload.get("type") == "heartbeat":
                await websocket.send_json({"type":"heartbeat","ts":payload.get("ts")})
            elif payload.get("type") == "subscribe":
                symbol = str(payload.get("symbol","")).upper()
                timeframe = str(payload.get("timeframe","5m"))
                if not symbol or len(symbol) > 32:
                    await websocket.send_json({"type":"error","message":"Invalid symbol"})
                else:
                    await websocket.send_json({"type":"subscribed","symbol":symbol,"timeframe":timeframe})
            else:
                await websocket.send_json({"type":"error","message":"Unsupported stream message"})
    except WebSocketDisconnect:
        pass
    finally:
        async with _lock:
            _clients.discard(websocket)
