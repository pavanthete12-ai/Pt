import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.quantpulse_audit import QuantPulseAudit

async def record(session: AsyncSession, *, event_type: str, symbol: str, signal: str | None = None, price: float | None = None, details: dict | None = None) -> None:
    session.add(QuantPulseAudit(event_type=event_type, symbol=symbol.upper(), signal=signal, price=price, details=json.dumps(details or {}, sort_keys=True)))
    await session.commit()
