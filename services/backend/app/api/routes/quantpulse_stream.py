import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/quantpulse/stream", tags=["quantpulse-stream"])

@router.websocket("")
async def market_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send_json({"type":"error","message":"Expected JSON"})
                continue
            # The server relays only validated provider payloads; it never invents market prices.
            if payload.get("type") == "heartbeat":
                await websocket.send_json({"type":"heartbeat","ts":payload.get("ts")})
            elif payload.get("type") == "candle":
                required = {"symbol","timestamp","open","high","low","close","volume"}
                if not required.issubset(payload):
                    await websocket.send_json({"type":"error","message":"Incomplete candle payload"})
                    continue
                await websocket.send_json({"type":"candle_ack","symbol":str(payload["symbol"]).upper(),"timestamp":payload["timestamp"]})
            else:
                await websocket.send_json({"type":"error","message":"Unsupported stream message"})
    except WebSocketDisconnect:
        return
