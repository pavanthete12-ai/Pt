from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.upstox_adapter import UpstoxAdapter

router = APIRouter(prefix="/quantpulse/provider", tags=["quantpulse-provider"])

class LiveOrderRequest(BaseModel):
    instrument_token: str = Field(min_length=3, max_length=128)
    quantity: int = Field(gt=0, le=1_000_000)
    transaction_type: str = Field(pattern="^(BUY|SELL)$")
    product: str = Field(default="D", pattern="^(I|D|MTF)$")
    order_type: str = Field(default="MARKET", pattern="^(MARKET|LIMIT|SL|SL-M)$")
    price: float = Field(default=0, ge=0)
    trigger_price: float = Field(default=0, ge=0)

@router.get("/upstox/authorize")
async def upstox_authorize():
    try:
        return {"provider":"upstox","authorized_redirect_uri":await UpstoxAdapter().market_feed_authorize()}
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Upstox authorization failed: {exc}") from exc

@router.post("/upstox/order")
async def upstox_order(request: LiveOrderRequest):
    raise HTTPException(403, "Live execution is intentionally locked. Complete broker authentication, risk approval, paper-trading validation, and an explicit live-execution unlock before enabling this adapter.")
