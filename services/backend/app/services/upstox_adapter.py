"""Optional Upstox V3 adapter. Credentials are supplied only through environment variables."""
import os
import httpx

class UpstoxAdapter:
    base_url = "https://api.upstox.com/v3"
    order_url = "https://api-hft.upstox.com/v3"

    def __init__(self, access_token: str | None = None):
        self.access_token = access_token or os.getenv("UPSTOX_ACCESS_TOKEN")

    def _headers(self) -> dict[str, str]:
        if not self.access_token:
            raise RuntimeError("UPSTOX_ACCESS_TOKEN is not configured")
        return {"Authorization": f"Bearer {self.access_token}", "Accept": "application/json"}

    async def market_feed_authorize(self) -> str:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self.base_url}/feed/market-data-feed/authorize", headers=self._headers())
            response.raise_for_status()
            return response.json()["data"]["authorized_redirect_uri"]

    async def place_order(self, *, instrument_token: str, quantity: int, transaction_type: str, product: str = "D", order_type: str = "MARKET", price: float = 0, trigger_price: float = 0, tag: str = "quantpulse", slice_order: bool = True) -> dict:
        payload = {
            "quantity": quantity, "product": product, "validity": "DAY", "price": price,
            "tag": tag, "instrument_token": instrument_token, "order_type": order_type,
            "transaction_type": transaction_type, "disclosed_quantity": 0,
            "trigger_price": trigger_price, "is_amo": False, "slice": slice_order,
            "market_protection": -1,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{self.order_url}/order/place", headers={**self._headers(), "Content-Type": "application/json"}, json=payload)
            response.raise_for_status()
            return response.json()
