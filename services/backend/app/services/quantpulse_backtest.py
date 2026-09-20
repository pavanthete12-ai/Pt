from dataclasses import dataclass
from app.services.quantpulse_engine import Candle, analyze

@dataclass(frozen=True)
class BacktestResult:
    trades: int
    wins: int
    losses: int
    net_pnl: float
    max_drawdown: float

def run_backtest(candles: list[Candle], initial_capital: float = 100000.0, risk_fraction: float = 0.01) -> BacktestResult:
    if len(candles) < 30:
        raise ValueError("At least 30 candles are required")
    capital = initial_capital
    peak = capital
    max_dd = 0.0
    wins = losses = 0
    for i in range(20, len(candles) - 1):
        signal = analyze(candles[:i+1])
        entry = candles[i+1].open
        if signal["signal"] == "HOLD":
            continue
        stop = signal["stop_loss"]
        target = signal["target"]
        distance = abs(entry - stop)
        if distance <= 0:
            continue
        qty = max(1, int((capital * risk_fraction) / distance))
        exit_price = candles[i+1].close
        pnl = (exit_price - entry) * qty if signal["signal"] == "BUY" else (entry - exit_price) * qty
        capital += pnl
        if pnl >= 0: wins += 1
        else: losses += 1
        peak = max(peak, capital)
        max_dd = max(max_dd, peak - capital)
    return BacktestResult(wins + losses, wins, losses, round(capital - initial_capital,2), round(max_dd,2))
