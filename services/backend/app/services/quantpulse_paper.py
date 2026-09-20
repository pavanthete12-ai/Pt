from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.paper_trading import PaperOrder

async def create_order(session: AsyncSession, *, symbol: str, side: str, quantity: float, entry_price: float, stop_loss: float, target: float) -> PaperOrder:
    order = PaperOrder(symbol=symbol.upper(), side=side.upper(), quantity=quantity, entry_price=entry_price, stop_loss=stop_loss, target=target)
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order

async def list_orders(session: AsyncSession, symbol: str | None = None) -> list[PaperOrder]:
    stmt = select(PaperOrder).order_by(PaperOrder.id.desc())
    if symbol:
        stmt = stmt.where(PaperOrder.symbol == symbol.upper())
    return list((await session.execute(stmt)).scalars().all())

async def close_order(session: AsyncSession, order: PaperOrder, exit_price: float) -> PaperOrder:
    if order.status != "OPEN":
        raise ValueError("Order is already closed")
    multiplier = 1 if order.side == "BUY" else -1
    order.realized_pnl = round((exit_price - order.entry_price) * order.quantity * multiplier, 2)
    order.status = "CLOSED"
    order.closed_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(order)
    return order
