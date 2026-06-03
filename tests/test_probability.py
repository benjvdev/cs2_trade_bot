import sqlite3

import pytest

from app.core import probability
from app.core.contracts import ContractEngine


def create_skins_db(tmp_path, outcomes):
    db_path = tmp_path / "skins.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE skins (
            id TEXT PRIMARY KEY,
            name TEXT,
            rarity TEXT,
            collection TEXT,
            min_float REAL,
            max_float REAL,
            image_url TEXT
        )
        """
    )
    cursor.executemany(
        """
        INSERT INTO skins (id, name, rarity, collection, min_float, max_float)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        outcomes,
    )
    conn.commit()
    conn.close()
    return db_path


def test_simulate_contract_probabilities_reads_from_supplied_db_path(tmp_path):
    collection = "__pytest_probability_collection__"
    db_path = create_skins_db(
        tmp_path,
        [
            ("pytest_outcome_1", "Pytest Outcome One", "Restricted", collection, 0.0, 1.0),
            ("pytest_outcome_2", "Pytest Outcome Two", "Restricted", collection, 0.0, 0.8),
        ],
    )
    inputs = [{"collection": collection, "rarity": "Mil-Spec Grade"} for _ in range(10)]

    outcomes = probability.simulate_contract_probabilities(inputs, db_path=str(db_path))

    assert {outcome["name"] for outcome in outcomes} == {
        "Pytest Outcome One",
        "Pytest Outcome Two",
    }
    assert [outcome["chance_percent"] for outcome in outcomes] == [
        pytest.approx(50.0),
        pytest.approx(50.0),
    ]


def test_simulate_contract_probabilities_requires_exactly_ten_inputs(tmp_path):
    collection = "__pytest_probability_collection__"
    db_path = create_skins_db(
        tmp_path,
        [("pytest_outcome_1", "Pytest Outcome One", "Restricted", collection, 0.0, 1.0)],
    )
    inputs = [{"collection": collection, "rarity": "Mil-Spec Grade"} for _ in range(9)]

    with pytest.raises(ValueError, match=r"^A trade-up contract requires exactly 10 inputs\.$"):
        probability.simulate_contract_probabilities(inputs, db_path=str(db_path))


def test_simulate_contract_probabilities_requires_matching_input_rarity(tmp_path):
    collection = "__pytest_probability_collection__"
    db_path = create_skins_db(
        tmp_path,
        [("pytest_outcome_1", "Pytest Outcome One", "Restricted", collection, 0.0, 1.0)],
    )
    inputs = [{"collection": collection, "rarity": "Mil-Spec Grade"} for _ in range(9)]
    inputs.append({"collection": collection, "rarity": "Industrial Grade"})

    with pytest.raises(ValueError, match=r"^All contract inputs must have the same rarity\.$"):
        probability.simulate_contract_probabilities(inputs, db_path=str(db_path))


def test_simulate_contract_probabilities_closes_connection_when_database_errors(monkeypatch):
    class BrokenCursor:
        def execute(self, *args):
            raise RuntimeError("database unavailable")

    class BrokenConnection:
        def __init__(self):
            self.closed = False

        def cursor(self):
            return BrokenCursor()

        def close(self):
            self.closed = True

    connection = BrokenConnection()
    monkeypatch.setattr(probability.sqlite3, "connect", lambda db_path: connection)
    inputs = [{"collection": "Any Collection", "rarity": "Mil-Spec Grade"} for _ in range(10)]

    with pytest.raises(RuntimeError, match="database unavailable"):
        probability.simulate_contract_probabilities(inputs, db_path="broken.db")

    assert connection.closed is True


def test_simulate_contract_probabilities_closes_connection_when_cursor_creation_fails(monkeypatch):
    class BrokenConnection:
        def __init__(self):
            self.closed = False

        def cursor(self):
            raise RuntimeError("cursor unavailable")

        def close(self):
            self.closed = True

    connection = BrokenConnection()
    monkeypatch.setattr(probability.sqlite3, "connect", lambda db_path: connection)
    inputs = [{"collection": "Any Collection", "rarity": "Mil-Spec Grade"} for _ in range(10)]

    with pytest.raises(RuntimeError, match="cursor unavailable"):
        probability.simulate_contract_probabilities(inputs, db_path="broken.db")

    assert connection.closed is True


def test_contract_engine_passes_db_path_to_probability_simulation(monkeypatch):
    class FakeDB:
        db_path = "custom-skins.db"

        def get_price(self, name, source):
            if name == "Pytest Input (Field-Tested)" and source == "steam":
                return 1.0
            return None

    captured = {}

    def fake_simulate(inputs, db_path=None):
        captured["db_path"] = db_path
        return []

    monkeypatch.setattr(probability, "simulate_contract_probabilities", fake_simulate)
    inputs = [
        {
            "name": "Pytest Input",
            "float": 0.2,
            "collection": "Any Collection",
            "rarity": "Mil-Spec Grade",
        }
        for _ in range(10)
    ]

    ContractEngine(FakeDB()).calculate_contract_profitability(inputs)

    assert captured["db_path"] == "custom-skins.db"
