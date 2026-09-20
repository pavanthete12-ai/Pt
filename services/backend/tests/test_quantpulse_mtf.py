from datetime import datetime, timedelta, timezone

from app.services.quantpulse_engine import Candle
from app.services.quantpulse_mtf import MultiTimeframeAnalyzer, fuse_timeframes


def minute_candle(price: float, volume: float = 100.0) -> Candle:
    return Candle(
        open=price,
        high=price + 2,
        low=price - 1,
        close=price + 1,
        volume=volume,
    )


def test_higher_timeframe_aggregates_ohlcv():
    analyzer = MultiTimeframeAnalyzer(max_candles=250)
    base = datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc)

    for i in range(6):
        analyzer.update("TEST", minute_candle(100 + i, 10), base + timedelta(minutes=i))

    # 5m bucket 09:15-09:19 is finalized when the 09:20 candle arrives.
    analyzer.update("TEST", minute_candle(106, 20), base + timedelta(minutes=5))

    series = analyzer._candles["TEST"]["5m"]
    assert len(series) == 1
    aggregated = series[0]
    assert aggregated.open == 100
    assert aggregated.high == 106
    assert aggregated.low == 99
    assert aggregated.close == 105
    assert aggregated.volume == 50


def test_same_bucket_updates_instead_of_appending():
    analyzer = MultiTimeframeAnalyzer()
    base = datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc)

    analyzer.update("TEST", minute_candle(100), base)
    analyzer.update("TEST", minute_candle(101), base + timedelta(minutes=1))

    assert ("TEST", "5m") in analyzer._buckets
    assert analyzer._buckets[("TEST", "5m")].open == 100
    assert analyzer._buckets[("TEST", "5m")].close == 102
    assert len(analyzer._candles["TEST"]["5m"]) == 0


def test_fusion_uses_available_timeframes():
    analyses = {
        "5m": {"signal": "BUY", "confidence": 80, "trend": "Bullish", "data_quality": "OK"},
        "15m": {"signal": "BUY", "confidence": 75, "trend": "Bullish", "data_quality": "OK"},
    }
    result = fuse_timeframes(analyses)
    assert result["signal"] == "BUY"
    assert result["agreement"] == 100.0


def test_fusion_returns_hold_without_data():
    result = fuse_timeframes({})
    assert result["signal"] == "HOLD"
    assert result["confidence"] == 0.0
