from app.services.quantpulse_market_intelligence import UpstoxMarketIntelligenceProvider


def test_pcr_parser(monkeypatch):
    provider = UpstoxMarketIntelligenceProvider("token")

    def fake_get(base, path, params):
        assert path == "/market/pcr"
        return {"data": {"pcr": 1.18}}

    monkeypatch.setattr(provider, "_get", fake_get)
    assert provider._pcr("NSE_INDEX|Nifty 50", "current_week", "2026-09-21") == 1.18


def test_oi_parser(monkeypatch):
    provider = UpstoxMarketIntelligenceProvider("token")

    def fake_get(base, path, params):
        return {"data": {"total_puts": 120, "total_calls": 100, "spot_closing_price": 25000}}

    monkeypatch.setattr(provider, "_get", fake_get)
    assert provider._oi("NSE_INDEX|Nifty 50", "current_week", "2026-09-21") == (120.0, 100.0, 25000.0)


def test_max_pain_parser(monkeypatch):
    provider = UpstoxMarketIntelligenceProvider("token")

    def fake_get(base, path, params):
        return {"data": {"max_pain": 24900}}

    monkeypatch.setattr(provider, "_get", fake_get)
    assert provider._max_pain("NSE_INDEX|Nifty 50", "current_week", "2026-09-21") == 24900.0


def test_snapshot_never_fabricates(monkeypatch):
    provider = UpstoxMarketIntelligenceProvider("token")

    def unavailable(*args, **kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr(provider, "_pcr", unavailable)
    monkeypatch.setattr(provider, "_oi", unavailable)
    monkeypatch.setattr(provider, "_max_pain", unavailable)
    monkeypatch.setattr(provider, "_india_vix", unavailable)

    snapshot = provider.snapshot("NSE_INDEX|Nifty 50")
    assert snapshot.status == "unavailable"
    assert snapshot.pcr is None
    assert snapshot.india_vix is None
