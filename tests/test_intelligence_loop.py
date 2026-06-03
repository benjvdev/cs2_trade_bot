from app.core import intelligence_loop
from app.core.config import Settings


class FakeContractEngine:
    def __init__(self, *args, **kwargs):
        pass

    def hunt_contracts(self, *args, **kwargs):
        return []


def test_run_continuous_loop_verifies_actual_batch_names(monkeypatch):
    opportunity_name = "AK-47 | Slate (Field-Tested)"
    seen = []

    monkeypatch.setattr(
        intelligence_loop.arbitrage,
        "find_arbitrage_opportunities",
        lambda **kwargs: [{"name": opportunity_name, "profit": 1}],
    )

    def collect_csfloat_names(*, limit, settings, market_hash_names=None):
        seen.extend(market_hash_names or [])
        return True

    monkeypatch.setattr(
        intelligence_loop.csfloat,
        "fetch_csfloat_prices",
        collect_csfloat_names,
    )
    monkeypatch.setattr(
        intelligence_loop.steam,
        "fetch_steam_prices",
        lambda limit: True,
    )
    monkeypatch.setattr(
        intelligence_loop.daily_dump,
        "fetch_daily_dumps",
        lambda: {"dump_buff": True},
    )
    monkeypatch.setattr(intelligence_loop.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(intelligence_loop, "DBManager", lambda: object())
    monkeypatch.setattr(intelligence_loop, "ContractEngine", FakeContractEngine)
    monkeypatch.setattr(intelligence_loop.subprocess, "run", lambda *args, **kwargs: None)

    settings = Settings(buff_session="", batch_size=1, batch_sleep=0)

    intelligence_loop.run_continuous_loop(settings, max_cycles=1)

    assert seen == [opportunity_name]
