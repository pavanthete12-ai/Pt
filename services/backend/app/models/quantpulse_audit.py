from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class QuantPulseAudit(Base):
    __tablename__ = "quantpulse_audit"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    signal: Mapped[str | None] = mapped_column(String(8), nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
