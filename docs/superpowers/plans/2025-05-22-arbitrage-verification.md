# Arbitrage Logic Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor arbitrage for testability via dependency injection and add verification tests for financial calculations.

**Architecture:** 
- Enhance `DBManager` with a `get_all_prices` method to encapsulate SQL.
- Refactor `find_arbitrage_opportunities` to use the injected `DBManager` instance.
- Implement unit tests using mocks to verify ROI and fee calculations for Steam (15%), CSFloat (2%), and Buff (2.5%).

**Tech Stack:** Python, pytest, unittest.mock

---

### Task 1: Enhance DBManager

**Files:**
- Modify: `app/database/db_manager.py`

- [ ] **Step 1: Add get_all_prices method**
```python
    def get_all_prices(self):
        """Returns all prices as a list of tuples (market_hash_name, price, source)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT market_hash_name, price, source FROM prices')
        rows = cursor.fetchall()
        conn.close()
        return rows
```

- [ ] **Step 2: Commit**
```bash
git add app/database/db_manager.py
git commit -m "feat: add get_all_prices to DBManager"
```

### Task 2: Refactor find_arbitrage_opportunities

**Files:**
- Modify: `app/core/arbitrage.py`

- [ ] **Step 1: Update signature and implementation**
```python
from app.database.db_manager import DBManager

def find_arbitrage_opportunities(rmb_to_usd=0.14, db_manager=None):
    """
    Identifies arbitrage opportunities where an item can be bought low on one market 
    and sold for a net profit on another.
    """
    if db_manager is None:
        db_manager = DBManager()
    
    try:
        rows = db_manager.get_all_prices()
    except Exception as e:
        bot_logger.error(f"Database error in arbitrage engine: {e}")
        return []
    # ... rest of the logic ...
```

- [ ] **Step 2: Commit**
```bash
git add app/core/arbitrage.py
git commit -m "refactor: inject DBManager into find_arbitrage_opportunities"
```

### Task 3: Implement Arbitrage Tests

**Files:**
- Create: `tests/test_arbitrage.py`

- [ ] **Step 1: Write the failing test**
Create a test that verifies ROI calculation and fees.

```python
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
```

- [ ] **Step 2: Run test to verify it fails**
It should pass if logic is already correct, but I'll watch it run.

- [ ] **Step 3: Run all tests to confirm**
```bash
pytest tests/test_arbitrage.py -v
```

- [ ] **Step 4: Commit**
```bash
git add tests/test_arbitrage.py
git commit -m "test: add arbitrage logic verification"
```
