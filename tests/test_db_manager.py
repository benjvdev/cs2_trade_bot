import pytest

from app.database.db_manager import DBManager


def test_get_all_price_records_returns_dict_rows_after_batch_update(tmp_path):
    db = DBManager(str(tmp_path / "prices.db"))
    db.update_prices_batch(
        [
            ("AK-47 | Slate (Field-Tested)", 1.23, "steam"),
            ("AK-47 | Slate (Field-Tested)", 1.11, "csfloat"),
        ]
    )

    records = db.get_all_price_records()

    assert len(records) == 2
    record = next(
        row
        for row in records
        if row["market_hash_name"] == "AK-47 | Slate (Field-Tested)"
        and row["source"] == "steam"
    )
    assert set(record) >= {"market_hash_name", "price", "source", "updated_at"}
    assert record["price"] == pytest.approx(1.23)
    assert record["updated_at"]


def test_get_price_map_groups_prices_by_item_and_source(tmp_path):
    db = DBManager(str(tmp_path / "prices.db"))
    db.update_prices_batch(
        [
            ("AK-47 | Slate (Field-Tested)", 1.23, "steam"),
            ("AK-47 | Slate (Field-Tested)", 1.11, "csfloat"),
            ("M4A1-S | Emphorosaur-S (Minimal Wear)", 4.56, "skinport"),
        ]
    )

    price_map = db.get_price_map()

    assert price_map["AK-47 | Slate (Field-Tested)"]["steam"]["price"] == pytest.approx(1.23)
    assert price_map["AK-47 | Slate (Field-Tested)"]["steam"]["updated_at"]
    assert price_map["AK-47 | Slate (Field-Tested)"]["csfloat"]["price"] == pytest.approx(1.11)
    assert price_map["M4A1-S | Emphorosaur-S (Minimal Wear)"]["skinport"]["price"] == pytest.approx(4.56)
