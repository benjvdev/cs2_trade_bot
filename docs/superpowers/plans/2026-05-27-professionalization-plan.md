# CS2 Trade Bot Professionalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up the project structure, implement Pydantic-based configuration validation, add type hints, and establish a comprehensive Pytest suite.

**Architecture:** 
- Reorganization: Move legacy scripts to `scripts/legacy/` and delete temporary files.
- Robustness: Use Pydantic for `config.json` validation and implement rotating logs.
- Testing: TDD approach for core math and probability engines using `pytest` and in-memory SQLite.

**Tech Stack:** Python, Pydantic, Pytest, SQLite.

---

### Task 1: Directory Cleanup and Reorganization

**Files:**
- Create: `scripts/legacy/`
- Create: `logs/`
- Modify: `app/main.py` (ensure imports reflect current structure)
- Delete: `check_p90.py`, `check_prices.py`, `check_sources.py`, `manual_tester.py`, `manual_verify.py`

- [ ] **Step 1: Create directories**

Run: `mkdir scripts/legacy`, `mkdir logs`

- [ ] **Step 2: Move legacy scripts**

Run:
```bash
mv db_builder.py scripts/legacy/
mv price_fetcher.py scripts/legacy/
mv hunter.py scripts/legacy/
mv profit_engine.py scripts/legacy/
mv contract_simulator.py scripts/legacy/
mv hunter_results.txt reports/
```

- [ ] **Step 3: Remove temporary scripts**

Run: `rm check_p90.py check_prices.py check_sources.py manual_tester.py manual_verify.py`

- [ ] **Step 4: Update .gitignore**

Modify: `.gitignore` to include `logs/` and ignore temporary test databases.

```text
logs/
data/test_*.db
```

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "chore: cleanup project structure and move legacy scripts"
```

---

### Task 2: Robust Configuration with Pydantic

**Files:**
- Create: `app/core/config.py`
- Modify: `app/main.py`
- Modify: `app/scrapers/csfloat.py`

- [ ] **Step 1: Install Pydantic**

Run: `pip install pydantic`

- [ ] **Step 2: Create Settings model**

```python
from pydantic import BaseModel, Field
from typing import Optional
import json
import os

class Settings(BaseModel):
    min_roi: float = Field(default=15.0, ge=0)
    max_budget: float = Field(default=50.0, ge=0)
    buff_session: str = Field(default="")
    steam_limit: int = Field(default=50, ge=1)
    csfloat_limit: int = Field(default=50, ge=1)
    rmb_to_usd: float = Field(default=0.14, gt=0)
    csfloat_api_key: str = Field(default="")
    batch_size: int = Field(default=50, ge=1)
    batch_sleep: int = Field(default=60, ge=0)

def load_settings(path: str = "config.json") -> Settings:
    if not os.path.exists(path):
        return Settings()
    with open(path, "r") as f:
        data = json.load(f)
    return Settings(**data)
```

- [ ] **Step 3: Update app/main.py to use Settings**

Replace `load_config()` calls with `load_settings()`.

- [ ] **Step 4: Commit**

```bash
git add app/core/config.py app/main.py
git commit -m "feat: add pydantic settings validation"
```

---

### Task 3: Professional Logging System

**Files:**
- Create: `app/utils/logger.py`
- Modify: `app/main.py`

- [ ] **Step 1: Create logger utility**

```python
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger():
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("cs2_bot")
    logger.setLevel(logging.INFO)
    
    # Console Handler
    c_handler = logging.StreamHandler()
    c_format = logging.Formatter('%(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    
    # File Handler
    f_handler = RotatingFileHandler("logs/bot.log", maxBytes=10*1024*1024, backupCount=5)
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)
    
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    return logger

bot_logger = setup_logger()
```

- [ ] **Step 2: Integrate logger in main.py**

Replace `print` statements with `bot_logger.info` or `bot_logger.error`.

- [ ] **Step 3: Commit**

```bash
git add app/utils/logger.py app/main.py
git commit -m "feat: implement professional rotating logging"
```

---

### Task 4: Math Engine Testing (TDD)

**Files:**
- Create: `tests/test_math_engine.py`
- Modify: `app/core/math_engine.py` (add type hints)

- [ ] **Step 1: Write tests for float precision**

```python
from app.core.math_engine import calculate_outcome_float, get_wear_name

def test_calculate_outcome_float_basic():
    inputs = [{'float': 0.10, 'min_float': 0.0, 'max_float': 1.0}] * 10
    # avg_norm = 0.10. outcome = (1.0-0.0)*0.10 + 0.0 = 0.10
    res = calculate_outcome_float(inputs, 0.0, 1.0)
    assert abs(res - 0.10) < 1e-6

def test_get_wear_name():
    assert get_wear_name(0.01) == "Factory New"
    assert get_wear_name(0.10) == "Minimal Wear"
    assert get_wear_name(0.20) == "Field-Tested"
```

- [ ] **Step 2: Add Type Hints to math_engine.py**

```python
def calculate_outcome_float(inputs_data: list[dict], outcome_min: float, outcome_max: float) -> float:
    # ... implementation
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_math_engine.py`

- [ ] **Step 4: Commit**

```bash
git add tests/test_math_engine.py app/core/math_engine.py
git commit -m "test: add math engine tests and type hints"
```

---

### Task 5: Arbitrage Logic Verification

**Files:**
- Create: `tests/test_arbitrage.py`
- Modify: `app/core/arbitrage.py` (refactor for testability)

- [ ] **Step 1: Refactor arbitrage for dependency injection**

Modify `find_arbitrage_opportunities` to accept a `db_manager` instance instead of creating one.

- [ ] **Step 2: Write tests with mock DB**

```python
from app.core.arbitrage import find_arbitrage_opportunities
from unittest.mock import MagicMock

def test_arbitrage_profit_calculation():
    mock_db = MagicMock()
    # Simulate DB data
    # ... (details omitted for brevity in summary, but full in actual task)
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_arbitrage.py app/core/arbitrage.py
git commit -m "test: add arbitrage logic verification"
```
