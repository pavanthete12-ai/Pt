from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.services.quantpulse_paper import close_order, create_order, list_orders

router = APIRouter(prefix="/quantpulse/paper", tags=["quantpulse-paper"])

class PaperOrderRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    side: str = Field(pattern="^(BUY|SELL)$")
    quantity: float = Field(gt=0, le=1_000_000)
    entry_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    target: float = Field(gt=0)

class CloseOrderRequest(BaseModel):
    exit_price: float = Field(gt=0)

def serialize(order):
    return {"id": order.id, "symbol": order.symbol, "side": order.side, "quantity": order.quantity, "entry_price": order.entry_price, "stop_loss": order.stop_loss, "target": order.target, "status": order.status, "created_at": order.created_at, "closed_at": order.closed_at, "realized_pnl": order.realized_pnl}

@router.post("/orders", status_code=201)
async def create_paper_order(request: PaperOrderRequest, session: AsyncSession = Depends(get_session)):
    if request.side == "BUY" and request.stop_loss >= request.entry_price:
        raise HTTPException(422, "BUY stop loss must be below entry price")
    if request.side == "SELL" and request.stop_loss <= request.entry_price:
        raise HTTPException(422, "SELL stop loss must be above entry price")
    order = await create_order(session, **request.model_dump())
    return serialize(order)

@router.get("/orders")
async def get_paper_orders(symbol: str | None = None, session: AsyncSession = Depends(get_session)):
    return {"orders": [serialize(x) for x in await list_orders(session, symbol)]}

@router.post("/orders/{order_id}/close")
async def close_paper_order(order_id: int, request: CloseOrderRequest, session: AsyncSession = Depends(get_session)):
    from sqlalchemy import select
    from app.models.paper_trading import PaperOrder
    order = (await session.execute(select(PaperOrder).where(PaperOrder.id == order_id))).scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Paper order not found")
    try:
        return serialize(await close_order(session, order, request.exit_price))
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
