# QuantPulse production path

## Implemented
- Deterministic technical/pattern fusion engine.
- OHLCV validation and normalization.
- Persistent SQLite paper orders.
- FastAPI paper-order endpoints.
- WebSocket transport for validated provider candle messages.
- Upstox V3 authorization adapter.
- Upstox V3 order payload adapter, deliberately locked behind the live-execution gate.

## Live market data
Upstox V3 provides an authorized WebSocket redirect and live market updates. The server must receive a user-authorized access token; credentials must never be committed to Git.

## Live execution gate
The live order endpoint currently returns HTTP 403 by design. Before enabling it, implement and verify:
1. OAuth/token lifecycle and encrypted secret storage.
2. Account/user binding and broker consent.
3. Max order value, max position, max daily loss, and leverage limits.
4. Mandatory stop-loss policy and kill switch.
5. Idempotency keys and duplicate-order protection.
6. Slippage/fee checks and exchange-session validation.
7. Full immutable audit log.
8. Paper-trading and out-of-sample validation.
9. Explicit user confirmation immediately before every live order.
10. Operational monitoring and incident rollback.

QuantPulse confidence is model strength, not a probability of profit and never a guarantee of returns.
