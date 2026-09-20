from dataclasses import dataclass

@dataclass(frozen=True)
class RiskLimits:
    max_order_value: float = 100000.0
    max_position_quantity: float = 1000.0
    max_daily_loss: float = 5000.0

def validate_order(*, side: str, quantity: float, entry_price: float, stop_loss: float, limits: RiskLimits) -> None:
    if quantity <= 0 or quantity > limits.max_position_quantity:
        raise ValueError("Quantity exceeds risk limit")
    if entry_price * quantity > limits.max_order_value:
        raise ValueError("Order value exceeds risk limit")
    if side == "BUY" and stop_loss >= entry_price:
        raise ValueError("BUY requires stop loss below entry")
    if side == "SELL" and stop_loss <= entry_price:
        raise ValueError("SELL requires stop loss above entry")
