import pytest
from unittest.mock import MagicMock

import sqlite3

from app.core import contracts
from app.core.contracts import ContractEngine


class PriceDB:
    def __init__(self, prices):
        self.prices = prices
        self.db_path = None

    def get_price(self, name, source):
        return self.prices.get((name, source))


def test_get_lowest_price():
    db_manager = MagicMock()
    # Mocking prices for "AK-47 | Slate (Field-Tested)"
    # Buff: 10 CNY -> 10 * 0.14 = 1.40 USD
    # Steam: 2.00 USD
    # CSFloat: 1.50 USD
    db_manager.get_price.side_effect = lambda name, source: {
        ('AK-47 | Slate (Field-Tested)', 'buff'): 10.0,
        ('AK-47 | Slate (Field-Tested)', 'steam'): 2.0,
        ('AK-47 | Slate (Field-Tested)', 'csfloat'): 1.5
    }.get((name, source))

    engine = ContractEngine(db_manager)
    price = engine.get_lowest_price("AK-47 | Slate", "Field-Tested")
    assert price == pytest.approx(1.40) # Buff is lowest


def test_get_lowest_price_uses_dump_fallback_and_converts_buff():
    db_manager = MagicMock()
    db_manager.get_price.side_effect = lambda name, source: {
        ('AK-47 | Slate (Field-Tested)', 'dump_steam'): 2.0,
        ('AK-47 | Slate (Field-Tested)', 'dump_buff'): 10.0,
    }.get((name, source))

    engine = ContractEngine(db_manager)

    assert engine.get_lowest_price("AK-47 | Slate", "Field-Tested") == pytest.approx(1.40)


def test_calculate_contract_profitability_uses_dump_fallback_for_outcome_sell_price(monkeypatch):
    def fake_simulate_contract_probabilities(inputs, db_path=None):
        return [
            {
                "name": "M4A4 | Desolate Space",
                "chance_percent": 100.0,
                "min_float": 0.0,
                "max_float": 1.0,
                "collection": "Gamma",
            }
        ]

    monkeypatch.setattr(
        contracts.probability,
        "simulate_contract_probabilities",
        fake_simulate_contract_probabilities,
    )
    db_manager = PriceDB(
        {
            ("AK-47 | Slate (Field-Tested)", "steam"): 1.0,
            ("M4A4 | Desolate Space (Field-Tested)", "dump_steam"): 20.0,
        }
    )
    inputs = [
        {
            "name": "AK-47 | Slate",
            "float": 0.2,
            "min_float": 0.0,
            "max_float": 1.0,
            "collection": "Snakebite",
            "rarity": "Mil-Spec Grade",
        }
        for _ in range(10)
    ]

    report = ContractEngine(db_manager).calculate_contract_profitability(inputs)

    assert "error" not in report
    assert report["cost"] == pytest.approx(10.0)
    assert report["revenue"] == pytest.approx(17.0)
    assert report["outcomes"][0]["max_net_revenue"] == pytest.approx(17.0)
    assert report["outcomes"][0]["best_market"] == "dump_steam"


def test_get_lowest_price_uses_price_map_once_without_get_price():
    class MapOnlyDB:
        def __init__(self):
            self.get_price_map_calls = 0
            self.get_price_calls = []

        def get_price_map(self):
            self.get_price_map_calls += 1
            return {
                "AK-47 | Slate (Field-Tested)": {
                    "dump_steam": {"price": 2.0},
                    "dump_buff": {"price": 10.0},
                }
            }

        def get_price(self, name, source):
            self.get_price_calls.append((name, source))
            return None

    db_manager = MapOnlyDB()
    engine = ContractEngine(db_manager)

    assert engine.get_lowest_price("AK-47 | Slate", "Field-Tested") == pytest.approx(1.40)
    assert engine.get_lowest_price("AK-47 | Slate", "Field-Tested") == pytest.approx(1.40)
    assert db_manager.get_price_map_calls == 1
    assert ("AK-47 | Slate (Field-Tested)", "dump_steam") not in db_manager.get_price_calls
    assert ("AK-47 | Slate (Field-Tested)", "dump_buff") not in db_manager.get_price_calls


def test_lookup_price_falls_back_to_db_when_price_map_misses_source():
    class PartialMapDB:
        def get_price_map(self):
            return {
                "AK-47 | Slate (Field-Tested)": {
                    "steam": {"price": 2.0},
                }
            }

        def get_price(self, name, source):
            return {
                ("AK-47 | Slate (Field-Tested)", "csfloat"): 1.5,
            }.get((name, source))

    engine = ContractEngine(PartialMapDB())

    assert engine._lookup_price("AK-47 | Slate (Field-Tested)", "csfloat") == pytest.approx(1.5)


def test_authoritative_price_map_miss_does_not_fall_back_to_db():
    class RealLikeMapDB:
        def __init__(self):
            self.get_price_calls = []

        def get_price_map(self):
            return {
                "AK-47 | Slate (Field-Tested)": {
                    "steam": {"price": 2.0},
                }
            }

        def get_all_price_records(self):
            return []

        def get_price(self, name, source):
            self.get_price_calls.append((name, source))
            return 1.5

    db_manager = RealLikeMapDB()
    engine = ContractEngine(db_manager)

    assert engine._lookup_price("AK-47 | Slate (Field-Tested)", "csfloat") is None
    assert db_manager.get_price_calls == []


def test_evaluate_combo_requires_filler_when_filler_count_is_positive():
    engine = ContractEngine(PriceDB({}))

    with pytest.raises(ValueError, match="filler is required"):
        engine._evaluate_combo(
            [],
            {"name": "Skin A", "collection": "Collection A", "rarity": "Mil-Spec Grade"},
            None,
            9,
            1,
            min_roi=1.0,
        )


def test_hunt_contracts_evaluates_10x_once_per_target_and_records_inputs(tmp_path):
    db_path = tmp_path / "contracts.db"
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE skins (
                id TEXT PRIMARY KEY,
                name TEXT,
                collection TEXT,
                rarity TEXT,
                min_float REAL,
                max_float REAL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE prices (
                market_hash_name TEXT,
                price REAL,
                source TEXT
            )
            """
        )
        skins = [
            ("skin-a", "Skin A", "Collection A", "Mil-Spec Grade", 0.0, 1.0),
            ("skin-b", "Skin B", "Collection B", "Mil-Spec Grade", 0.0, 1.0),
            ("skin-c", "Skin C", "Collection C", "Mil-Spec Grade", 0.0, 1.0),
        ]
        cursor.executemany(
            "INSERT INTO skins (id, name, collection, rarity, min_float, max_float) VALUES (?, ?, ?, ?, ?, ?)",
            skins,
        )
        cursor.executemany(
            "INSERT INTO prices (market_hash_name, price, source) VALUES (?, ?, ?)",
            [
                ("Skin A (Field-Tested)", 1.0, "dump_steam"),
                ("Skin B (Field-Tested)", 2.0, "dump_steam"),
                ("Skin C (Field-Tested)", 3.0, "dump_steam"),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    class HuntDB:
        def __init__(self, path):
            self.db_path = str(path)

    class ReportingEngine(ContractEngine):
        def calculate_contract_profitability(self, inputs):
            return {
                "cost": 10.0,
                "revenue": 20.0,
                "profit": 10.0,
                "roi": 100.0,
                "outcomes": [],
            }

    reports = ReportingEngine(HuntDB(db_path)).hunt_contracts(min_roi=1.0, max_budget=25.0)

    assert len(reports) == 15
    ten_x_reports = [
        report
        for report in reports
        if report["inputs"]["target_count"] == 10 and report["inputs"]["filler_count"] == 0
    ]
    assert len(ten_x_reports) == 3
    assert all(report["inputs"]["filler"] is None for report in ten_x_reports)
    assert all(report["inputs"]["input_float"] == pytest.approx(0.08) for report in reports)

    mixed_ratios = {
        (report["inputs"]["target_count"], report["inputs"]["filler_count"])
        for report in reports
        if report["inputs"]["filler"] is not None
    }
    assert mixed_ratios == {(9, 1), (5, 5)}
