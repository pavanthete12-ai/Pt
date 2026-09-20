from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper_trading import PaperOrder
from app.services.quantpulse_audit import record
from app.services.quantpulse_paper import close_order


async def daily_realized_pnl(session: AsyncSession, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    result = await session.execute(
        select(func.coalesce(func.sum(PaperOrder.realized_pnl), 0.0)).where(
            PaperOrder.status == "CLOSED",
            PaperOrder.closed_at >= day_start,
        )
    )
    return float(result.scalar_one() or 0.0)


async def open_orders(session: AsyncSession, symbol: str | None = None) -> list[PaperOrder]:
    stmt = select(PaperOrder).where(PaperOrder.status == "OPEN")
    if symbol:
        stmt = stmt.where(PaperOrder.symbol == symbol.upper())
    return list((await session.execute(stmt.order_by(PaperOrder.id.asc()))).scalars().all())


async def process_candle_for_paper_positions(
    session: AsyncSession,
    *,
    symbol: str,
    high: float,
    low: float,
    close: float,
) -> list[PaperOrder]:
    """Close paper positions when their stop or target is reached.

    If both levels are touched in the same candle, stop loss wins (conservative
    assumption because OHLC alone cannot establish intrabar ordering).
    """
    closed: list[PaperOrder] = []
    for order in await open_orders(session, symbol):
        exit_price = None
        reason = None
        if order.side == "BUY":
            if low <= order.stop_loss:
                exit_price, reason = order.stop_loss, "STOP_LOSS"
            elif high >= order.target:
                exit_price, reason = order.target, "TARGET"
        else:
            if high >= order.stop_loss:
                exit_price, reason = order.stop_loss, "STOP_LOSS"
            elif low <= order.target:
                exit_price, reason = order.target, "TARGET"

        if exit_price is not None:
            closed_order = await close_order(session, order, exit_price)
            await record(
                session,
                event_type="PAPER_POSITION_AUTO_CLOSED",
                symbol=closed_order.symbol,
                signal=closed_order.side,
                price=exit_price,
                details={
                    "order_id": closed_order.id,
                    "reason": reason,
                    "realized_pnl": closed_order.realized_pnl,
                },
            )
            closed.append(closed_order)
    return closed
