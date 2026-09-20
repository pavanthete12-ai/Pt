from fastapi import APIRouter, HTTPException, Query
from app.services.quantpulse_news import UpstoxNewsProvider

router = APIRouter(prefix="/quantpulse/news", tags=["quantpulse-news"])


@router.get("/{instrument_key:path}")
async def get_news(
    instrument_key: str,
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        return await UpstoxNewsProvider().analyze(instrument_key, page_size)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="News provider is not configured") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="News provider request failed") from exc
