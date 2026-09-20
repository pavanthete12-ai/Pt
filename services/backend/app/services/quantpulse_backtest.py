from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from app.services.quantpulse_engine import Candle, analyze


@dataclass(frozen=True)
class BacktestResult:
    trades: int
    wins: int
    losses: int
    net_pnl: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    expectancy: float
    final_capital: float
    fees: float
    slippage: float


def run_backtest(
    candles: list[Candle],
    initial_capital: float = 100000.0,
    risk_fraction: float = 0.01,
    fee_bps: float = 5.0,
    slippage_bps: float = 2.0,
) -> BacktestResult:
    if len(candles) < 30:
        raise ValueError("At least 30 candles are required")
    if initial_capital <= 0 or not 0 < risk_fraction <= 1:
        raise ValueError("Invalid capital or risk fraction")
    if fee_bps < 0 or slippage_bps < 0:
        raise ValueError("Fees and slippage cannot be negative")

    capital = initial_capital
    peak = capital
    max_dd = 0.0
    wins = losses = 0
    gross_profit = gross_loss = 0.0
    total_fees = total_slippage = 0.0

    for i in range(20, len(candles) - 1):
        signal = analyze(candles[: i + 1])
        if signal["signal"] == "HOLD":
            continue

        source = candles[i]
        next_candle = candles[i + 1]
        raw_entry = next_candle.open
        direction = 1 if signal["signal"] == "BUY" else -1
        slip_rate = slippage_bps / 10000.0
        entry = raw_entry * (1 + direction * slip_rate)

        stop_distance = abs(entry - signal["stop_loss"])
        if stop_distance <= 0:
            continue

        qty = max(1, int((capital * risk_fraction) / stop_distance))
        notional = entry * qty
        entry_fee = notional * fee_bps / 10000.0

        stop = signal["stop_loss"]
        target = signal["target"]

        if direction == 1:
            stop_hit = next_candle.low <= stop
            target_hit = next_candle.high >= target
        else:
            stop_hit = next_candle.high >= stop
            target_hit = next_candle.low <= target

        # Conservative OHLC assumption: if both levels are touched in one bar,
        # treat the stop as first because intrabar order is unknowable.
        if stop_hit:
            raw_exit = stop
        elif target_hit:
            raw_exit = target
        else:
            raw_exit = next_candle.close

        exit = raw_exit * (1 - direction * slip_rate)
        exit_notional = exit * qty
        exit_fee = exit_notional * fee_bps / 10000.0
        fees = entry_fee + exit_fee
        slippage_cost = abs(entry - raw_entry) * qty + abs(exit - raw_exit) * qty
        pnl = (exit - entry) * qty * direction - fees

        capital += pnl
        total_fees += fees
        total_slippage += slippage_cost

        if pnl >= 0:
            wins += 1
            gross_profit += pnl
        else:
            losses += 1
            gross_loss += abs(pnl)

        peak = max(peak, capital)
        max_dd = max(max_dd, peak - capital)

    trades = wins + losses
    win_rate = (wins / trades * 100.0) if trades else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss else (float("inf") if gross_profit else 0.0)
    expectancy = (capital - initial_capital) / trades if trades else 0.0

    return BacktestResult(
        trades=trades,
        wins=wins,
        losses=losses,
        net_pnl=round(capital - initial_capital, 2),
        max_drawdown=round(max_dd, 2),
        win_rate=round(win_rate, 2),
        profit_factor=round(profit_factor, 3) if profit_factor != float("inf") else profit_factor,
        expectancy=round(expectancy, 2),
        final_capital=round(capital, 2),
        fees=round(total_fees, 2),
        slippage=round(total_slippage, 2),
    )
