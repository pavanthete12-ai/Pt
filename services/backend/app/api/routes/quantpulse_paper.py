from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.services.quantpulse_paper import close_order, create_order, list_orders
from app.services.quantpulse_risk import RiskLimits, validate_order
from app.services.quantpulse_audit import record
from app.services.quantpulse_paper_manager import daily_realized_pnl

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
    try:
        validate_order(side=request.side, quantity=request.quantity, entry_price=request.entry_price, stop_loss=request.stop_loss, limits=RiskLimits())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    limits = RiskLimits()
    realized_today = await daily_realized_pnl(session)
    if realized_today <= -limits.max_daily_loss:
        raise HTTPException(429, "Daily loss limit reached; new paper orders are locked")
    order = await create_order(session, **request.model_dump())
    await record(session, event_type="PAPER_ORDER_CREATED", symbol=request.symbol, signal=request.side, price=request.entry_price, details=request.model_dump())
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
        closed = await close_order(session, order, request.exit_price)
        await record(session, event_type="PAPER_ORDER_CLOSED", symbol=closed.symbol, signal=closed.side, price=request.exit_price, details={"order_id": order_id, "realized_pnl": closed.realized_pnl})
        return serialize(closed)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
