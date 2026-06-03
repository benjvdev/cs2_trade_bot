import pytest
from unittest.mock import MagicMock
from app.core.arbitrage import find_arbitrage_opportunities

def test_arbitrage_roi_and_fees():
    mock_db = MagicMock()
    # Case: Buff ($10 RMB -> $1.40 USD) vs Steam ($2.00 USD)
    # Steam Fee: 15% -> Net Sell: 2.00 * 0.85 = $1.70
    # Buff Fee: 2.5% -> Buy: $1.40
    # Profit: 1.70 - 1.40 = 0.30
    # ROI: (0.30 / 1.40) * 100 = 21.43%
    
    # Case 2: CSFloat ($1.50) vs Steam ($2.00)
    # CSFloat Fee: 2% -> Net Sell: 1.50 * 0.98 = $1.47
    
    mock_db.get_all_prices.return_value = [
        ("AK-47 | Redline (Field-Tested)", 10.0, "buff"),
        ("AK-47 | Redline (Field-Tested)", 2.0, "steam"),
        ("AK-47 | Redline (Field-Tested)", 1.5, "csfloat")
    ]
    
    opps = find_arbitrage_opportunities(rmb_to_usd=0.14, db_manager=mock_db)
    
    # Find Buff -> Steam opportunity
    buff_to_steam = next(o for o in opps if o['buy_source'] == 'buff' and o['sell_source'] == 'steam')
    assert round(buff_to_steam['profit'], 2) == 0.30
    assert round(buff_to_steam['roi'], 2) == 21.43
    
    # Find CSFloat -> Steam opportunity
    # CSFloat Buy: 1.50
    # Steam Net: 1.70
    # Profit: 0.20
    # ROI: (0.20 / 1.50) * 100 = 13.33%
    csfloat_to_steam = next(o for o in opps if o['buy_source'] == 'csfloat' and o['sell_source'] == 'steam')
    assert round(csfloat_to_steam['profit'], 2) == 0.20
    assert round(csfloat_to_steam['roi'], 2) == 13.33


def test_arbitrage_excludes_untrusted_historical_sources():
    mock_db = MagicMock()
    mock_db.get_all_price_records.return_value = [
        {
            "market_hash_name": "AWP | Dragon Lore (Factory New)",
            "price": 1000.0,
            "source": "dump_buff",
            "updated_at": "2026-06-03T00:00:00Z",
        },
        {
            "market_hash_name": "AWP | Dragon Lore (Factory New)",
            "price": 10000.0,
            "source": "csgobackpack",
            "updated_at": "2026-06-03T00:00:00Z",
        },
    ]

    opps = find_arbitrage_opportunities(
        rmb_to_usd=0.14,
        db_manager=mock_db,
        trusted_sources={"steam", "csfloat", "buff", "dump_buff"},
    )

    assert opps == []


def test_arbitrage_default_trusted_sources_exclude_csgobackpack():
    mock_db = MagicMock()
    mock_db.get_all_price_records.return_value = [
        {
            "market_hash_name": "AWP | Dragon Lore (Factory New)",
            "price": 1000.0,
            "source": "dump_buff",
            "updated_at": "2026-06-03T00:00:00Z",
        },
        {
            "market_hash_name": "AWP | Dragon Lore (Factory New)",
            "price": 10000.0,
            "source": "csgobackpack",
            "updated_at": "2026-06-03T00:00:00Z",
        },
    ]

    opps = find_arbitrage_opportunities(rmb_to_usd=0.14, db_manager=mock_db)

    assert opps == []


def test_arbitrage_filters_by_min_roi():
    mock_db = MagicMock()
    mock_db.get_all_prices.return_value = [
        ("AK-47 | Redline (Field-Tested)", 10.0, "buff"),
        ("AK-47 | Redline (Field-Tested)", 2.0, "steam"),
        ("AK-47 | Redline (Field-Tested)", 1.5, "csfloat"),
    ]

    opps = find_arbitrage_opportunities(
        rmb_to_usd=0.14,
        db_manager=mock_db,
        min_roi=20,
    )

    assert any(
        o["buy_source"] == "buff" and o["sell_source"] == "steam"
        for o in opps
    )
    assert not any(
        o["buy_source"] == "csfloat" and o["sell_source"] == "steam"
        for o in opps
    )
