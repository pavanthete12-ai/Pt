from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services.quantpulse_market_intelligence import UpstoxMarketIntelligenceProvider

router = APIRouter(prefix="/quantpulse/market-intelligence", tags=["quantpulse-market-intelligence"])


@router.get("/{instrument_key:path}")
def market_intelligence(
    instrument_key: str,
    expiry: str = Query("current_week", min_length=1, max_length=32),
    as_of: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
):
    provider = UpstoxMarketIntelligenceProvider()
    try:
        snapshot = provider.snapshot(instrument_key, expiry=expiry, as_of=as_of)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Market intelligence provider is not configured") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Market intelligence provider request failed") from exc

    return {
        "instrument_key": snapshot.instrument_key,
        "as_of": snapshot.as_of,
        "pcr": snapshot.pcr,
        "total_put_oi": snapshot.total_put_oi,
        "total_call_oi": snapshot.total_call_oi,
        "max_pain": snapshot.max_pain,
        "spot_price": snapshot.spot_price,
        "india_vix": snapshot.india_vix,
        "status": snapshot.status,
        "source": snapshot.source,
        "notes": list(snapshot.notes),
    }
