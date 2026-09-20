import pytest
from app.services.quantpulse_engine import Candle, analyze

def _candles():
    return [Candle(100+i*0.2, 101+i*0.2, 99+i*0.2, 100.5+i*0.2, 1000) for i in range(30)]

def test_signal_is_deterministic():
    candles = _candles()
    assert analyze(candles) == analyze(candles)

def test_signal_has_risk_levels():
    result = analyze(_candles())
    assert result["stop_loss"] > 0
    assert result["target"] > 0
    assert result["risk_reward"] == 2.0
