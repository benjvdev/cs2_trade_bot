import pytest
from unittest.mock import MagicMock
from app.core.contracts import ContractEngine

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
    assert price == 1.40 # Buff is lowest
