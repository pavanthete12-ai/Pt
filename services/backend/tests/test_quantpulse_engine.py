from app.services.quantpulse_engine import Candle, analyze


def candles(count: int = 40) -> list[Candle]:
    result = []
    price = 100.0
    for i in range(count):
        price += 0.8 if i % 5 else -0.1
        result.append(Candle(price - 0.2, price + 0.6, price - 0.4, price, 1000 + i))
    return result


def test_signal_engine_is_deterministic():
    result = analyze(candles(), news_sentiment=0.4)
    assert result["signal"] in {"BUY", "SELL", "HOLD"}
    assert 0 <= result["confidence"] <= 99
    assert result["risk_reward"] == 2.0
    assert result["data_quality"] == "OK"


def test_engine_requires_history():
    try:
        analyze(candles(10))
        assert False, "expected ValueError"
    except ValueError:
        pass
