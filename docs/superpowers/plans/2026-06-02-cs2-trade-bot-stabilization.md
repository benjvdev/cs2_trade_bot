# CS2 Trade Bot Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stabilize the CS2 trade bot so its scrapers, database, arbitrage engine, contract engine, and continuous loop produce fresh, testable, actionable market intelligence.

**Architecture:** Keep the existing worker-engine shape, but make each scraper testable through dependency injection and structured results. Centralize DB access, add freshness/trust filters before analysis, and make live verification target the exact opportunity items instead of generic market pages.

**Tech Stack:** Python, pytest, Pydantic, SQLite, requests/cloudscraper, Node.js, Playwright, sqlite3.

---

## File Structure

- Create: `tests/test_csfloat_scraper.py`
- Create: `tests/test_db_manager.py`
- Create: `tests/test_config.py`
- Create: `tests/test_probability.py`
- Create: `tests/test_intelligence_loop.py`
- Modify: `requirements.txt`
- Modify: `app/core/config.py`
- Modify: `app/scrapers/csfloat.py`
- Modify: `app/scrapers/daily_dump.py`
- Modify: `app/scrapers/steam.py`
- Modify: `app/scrapers/buff/index.js`
- Modify: `app/database/db_manager.py`
- Modify: `app/core/arbitrage.py`
- Modify: `app/core/contracts.py`
- Modify: `app/core/probability.py`
- Modify: `app/core/intelligence_loop.py`
- Modify: `app/main.py`
- Modify: `README.md`
- Modify: `docs/design_spec.md`
- Optional cleanup after approval: remove tracked data with `git rm --cached cs2_skins.db prices.json`

## Implementation Rules

- Do not copy or print `config.json` secrets.
- Do not use `verify=False` as a production fix for HTTPS.
- Every external scraper fix starts with mocked unit tests.
- Live network checks must be separate smoke commands, not default tests.
- Report generation must refuse or clearly mark stale/incomplete source data.

### Task 1: Dependency And Secret Baseline

**Files:**
- Modify: `requirements.txt`
- Modify: `app/core/config.py`
- Create: `tests/test_config.py`
- Modify: `README.md`

- [ ] **Step 1: Write config tests**

Create `tests/test_config.py`:

```python
import json

from app.core.config import load_settings


def test_load_settings_accepts_example_extra_market_keys(tmp_path):
    config = {
        "min_roi": 15.0,
        "max_budget": 50.0,
        "buff_session": "example",
        "steam_limit": 50,
        "csfloat_limit": 50,
        "rmb_to_usd": 0.14,
        "csfloat_api_key": "example-key",
        "skinport_api_key": "skinport-key",
        "skinbaron_api_key": "skinbaron-key",
        "batch_size": 100,
        "batch_sleep": 5.0,
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    settings = load_settings(str(path))

    assert settings.skinport_api_key == "skinport-key"
    assert settings.skinbaron_api_key == "skinbaron-key"
    assert settings.batch_sleep == 5.0


def test_environment_overrides_secret_values(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "min_roi": 15.0,
                "max_budget": 50.0,
                "buff_session": "file-session",
                "csfloat_api_key": "file-key",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("BUFF_SESSION", "env-session")
    monkeypatch.setenv("CSFLOAT_API_KEY", "env-key")

    settings = load_settings(str(path))

    assert settings.buff_session == "env-session"
    assert settings.csfloat_api_key == "env-key"
```

- [ ] **Step 2: Run config tests and verify they fail**

Run:

```bash
python -m pytest tests/test_config.py -q
```

Expected:
- First test fails because `skinport_api_key` and `skinbaron_api_key` are ignored by `Settings`.
- Second test fails because environment overrides are not implemented.

- [ ] **Step 3: Update dependencies**

Change `requirements.txt` to:

```text
cloudscraper
requests
playwright
pydantic
pytest
```

- [ ] **Step 4: Implement complete settings model**

Update `app/core/config.py`:

```python
import json
import os
from typing import Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    min_roi: float = Field(15.0, ge=0)
    max_budget: float = Field(50.0, ge=0)
    buff_session: str = ""
    steam_limit: int = Field(50, gt=0)
    csfloat_limit: int = Field(50, gt=0)
    rmb_to_usd: float = Field(0.14, gt=0)
    csfloat_api_key: Optional[str] = None
    skinport_api_key: Optional[str] = None
    skinbaron_api_key: Optional[str] = None
    batch_size: int = Field(100, gt=0)
    batch_sleep: float = Field(5.0, ge=0)
    max_price_age_hours: float = Field(24.0, gt=0)


ENV_OVERRIDES = {
    "BUFF_SESSION": "buff_session",
    "CSFLOAT_API_KEY": "csfloat_api_key",
    "SKINPORT_API_KEY": "skinport_api_key",
    "SKINBARON_API_KEY": "skinbaron_api_key",
}


def load_settings(config_path: str = "config.json") -> Settings:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    for env_name, field_name in ENV_OVERRIDES.items():
        value = os.environ.get(env_name)
        if value:
            config_data[field_name] = value

    return Settings(**config_data)
```

- [ ] **Step 5: Run config tests**

Run:

```bash
python -m pytest tests/test_config.py -q
```

Expected:

```text
2 passed
```

- [ ] **Step 6: Rotate local secrets**

Action:
- Rotate the local CSFloat API key and Buff session if this workspace or logs have been shared.
- Keep new values in `config.json` or environment variables only.
- Do not commit `config.json`.

### Task 2: Fix CSFloat Scraper Root Cause

**Files:**
- Create: `tests/test_csfloat_scraper.py`
- Modify: `app/scrapers/csfloat.py`
- Modify: `app/main.py`

- [ ] **Step 1: Write failing CSFloat parser and scraper tests**

Create `tests/test_csfloat_scraper.py`:

```python
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.core.config import Settings
from app.scrapers import csfloat


class FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = {"content-type": "application/json"}

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def test_extract_listings_accepts_current_wrapped_payload():
    payload = {
        "data": [
            {
                "type": "buy_now",
                "state": "listed",
                "price": 12345,
                "item": {"market_hash_name": "AK-47 | Slate (Field-Tested)"},
            }
        ],
        "cursor": "next-page",
    }

    listings, cursor = csfloat.extract_listings(payload)

    assert len(listings) == 1
    assert cursor == "next-page"


def test_extract_listings_accepts_legacy_list_payload():
    payload = [
        {
            "type": "buy_now",
            "state": "listed",
            "price": 12345,
            "item": {"market_hash_name": "AK-47 | Slate (Field-Tested)"},
        }
    ]

    listings, cursor = csfloat.extract_listings(payload)

    assert len(listings) == 1
    assert cursor is None


def test_fetch_csfloat_prices_updates_db_from_wrapped_payload():
    response = FakeResponse(
        200,
        {
            "data": [
                {
                    "type": "buy_now",
                    "state": "listed",
                    "price": 12345,
                    "item": {"market_hash_name": "AK-47 | Slate (Field-Tested)"},
                }
            ],
            "cursor": None,
        },
    )
    scraper = MagicMock()
    scraper.get.return_value = response
    db = MagicMock()
    settings = Settings(buff_session="", csfloat_api_key="key")

    result = csfloat.fetch_csfloat_prices(
        limit=1,
        settings=settings,
        db_manager=db,
        scraper=scraper,
    )

    assert result is True
    db.update_prices_batch.assert_called_once_with(
        [("AK-47 | Slate (Field-Tested)", 123.45, "csfloat")]
    )
    called_url = scraper.get.call_args.args[0]
    assert "type=buy_now" in called_url
    assert "limit=1" in called_url


def test_fetch_csfloat_prices_rejects_non_json_response():
    scraper = MagicMock()
    scraper.get.return_value = FakeResponse(403, payload=None, text="<html>blocked</html>")
    db = MagicMock()

    result = csfloat.fetch_csfloat_prices(
        limit=1,
        settings=Settings(buff_session="", csfloat_api_key="key"),
        db_manager=db,
        scraper=scraper,
    )

    assert result is False
    db.update_prices_batch.assert_not_called()
```

- [ ] **Step 2: Run CSFloat tests and verify they fail**

Run:

```bash
python -m pytest tests/test_csfloat_scraper.py -q
```

Expected:
- Import or attribute failure for `extract_listings`.
- Existing `fetch_csfloat_prices` does not accept `db_manager` or `scraper`.

- [ ] **Step 3: Implement parser, injection, `buy_now`, and pagination**

Update `app/scrapers/csfloat.py`:

```python
from urllib.parse import urlencode

import cloudscraper

from app.core.config import Settings, load_settings
from app.database.db_manager import DBManager
from app.utils.logger import bot_logger


BASE_URL = "https://csfloat.com/api/v1/listings"


def extract_listings(payload):
    if isinstance(payload, list):
        return payload, None
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"], payload.get("cursor")
    raise ValueError("CSFloat response must be a list or an object with data[]")


def build_headers(settings: Settings | None):
    headers = {
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    api_key = settings.csfloat_api_key if settings else None
    if api_key:
        headers["Authorization"] = api_key
    return headers


def fetch_csfloat_prices(limit=50, settings: Settings = None, db_manager=None, scraper=None):
    if settings is None:
        try:
            settings = load_settings()
        except Exception as exc:
            bot_logger.warning(f"CSFloat settings unavailable: {exc}")
            settings = None

    scraper = scraper or cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )
    db = db_manager or DBManager()
    headers = build_headers(settings)
    remaining = max(1, int(limit))
    cursor = None
    batch_data = []

    bot_logger.info(f"Fetching up to {remaining} buy_now items from CSFloat...")

    while remaining > 0:
        page_limit = min(remaining, 50)
        params = {
            "limit": page_limit,
            "sort_by": "lowest_price",
            "type": "buy_now",
        }
        if cursor:
            params["cursor"] = cursor

        url = f"{BASE_URL}?{urlencode(params)}"
        try:
            response = scraper.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                bot_logger.error(f"CSFloat API error: {response.status_code}")
                return False
            payload = response.json()
            listings, cursor = extract_listings(payload)
        except Exception as exc:
            bot_logger.error(f"Error fetching CSFloat prices: {exc}")
            return False

        for listing in listings:
            if listing.get("state") != "listed":
                continue
            if listing.get("type") != "buy_now":
                continue
            item = listing.get("item") or {}
            hash_name = item.get("market_hash_name")
            price_cents = listing.get("price")
            if hash_name and price_cents is not None:
                batch_data.append((hash_name, float(price_cents) / 100.0, "csfloat"))

        remaining -= page_limit
        if not cursor:
            break

    if not batch_data:
        bot_logger.warning("No valid buy_now items found in CSFloat response.")
        return False

    db.update_prices_batch(batch_data)
    bot_logger.info(f"Successfully updated {len(batch_data)} items from CSFloat.")
    return True
```

- [ ] **Step 4: Make `main.py` observe scraper status**

In `app/main.py`, collect results:

```python
results = {
    "steam": steam.fetch_steam_prices(limit=steam_limit),
    "csfloat": csfloat.fetch_csfloat_prices(limit=csfloat_limit, settings=config),
}
failed = [name for name, ok in results.items() if not ok]
if failed:
    bot_logger.warning(f"Scrapers failed or returned no data: {', '.join(failed)}")
```

- [ ] **Step 5: Run CSFloat and full tests**

Run:

```bash
python -m pytest tests/test_csfloat_scraper.py tests/test_config.py -q
python -m pytest -q
```

Expected:

```text
all tests pass
```

- [ ] **Step 6: Run safe live CSFloat smoke**

Run:

```bash
python -c "from app.scrapers.csfloat import fetch_csfloat_prices; print(fetch_csfloat_prices(1))"
```

Expected:
- Prints `True`.
- DB gains at least one `csfloat` row.

### Task 3: Make Daily Dumps Observable And Safe

**Files:**
- Modify: `app/scrapers/daily_dump.py`
- Create: `tests/test_daily_dump.py` additions

- [ ] **Step 1: Add tests for 403 HTML and successful JSON**

Extend `tests/test_daily_dump.py`:

```python
def test_fetch_daily_dumps_does_not_parse_html_403(mock_db_class, mock_get):
    mock_db = MagicMock()
    mock_db_class.return_value = mock_db

    html_resp = MagicMock()
    html_resp.status_code = 403
    html_resp.headers = {"content-type": "text/html"}
    html_resp.text = "<html>blocked</html>"
    mock_get.return_value = html_resp

    result = fetch_daily_dumps()

    assert result["dump_buff"] is False
    assert result["dump_v6"] is False
    mock_db.update_prices_batch.assert_not_called()
```

- [ ] **Step 2: Run the daily dump tests and verify failure**

Run:

```bash
python -m pytest tests/test_daily_dump.py -q
```

Expected:
- New test fails because `fetch_daily_dumps()` returns `None`.

- [ ] **Step 3: Implement response validation**

Add to `app/scrapers/daily_dump.py`:

```python
def fetch_json(url, headers):
    response = requests.get(url, headers=headers, timeout=30)
    content_type = response.headers.get("content-type", "")
    if response.status_code != 200:
        raise RuntimeError(f"{url} returned HTTP {response.status_code}")
    if "json" not in content_type.lower():
        raise RuntimeError(f"{url} returned non-JSON content-type: {content_type}")
    return response.json()
```

Change `fetch_daily_dumps()` to:

```python
def fetch_daily_dumps():
    db = DBManager()
    status = {"dump_buff": False, "dump_v6": False}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        data = fetch_json(BUFF_URL, headers)
        batch = []
        for name, info in data.items():
            price = info.get("starting_at", {}).get("price")
            if price:
                batch.append((name, price, "dump_buff"))
        db.update_prices_batch(batch)
        status["dump_buff"] = True
    except Exception as exc:
        bot_logger.error(f"Error loading Buff dump: {exc}")

    try:
        data = fetch_json(V6_URL, headers)
        batches = {"dump_steam": [], "dump_skinport": [], "dump_skinbaron": []}
        for name, markets in data.items():
            steam_p = markets.get("steam", {}).get("last_24h")
            if steam_p:
                batches["dump_steam"].append((name, steam_p, "dump_steam"))
            sp_p = markets.get("skinport", {}).get("suggested_price")
            if sp_p:
                batches["dump_skinport"].append((name, sp_p, "dump_skinport"))
            sb_p = markets.get("skinbaron", {}).get("suggested_price")
            if sb_p:
                batches["dump_skinbaron"].append((name, sb_p, "dump_skinbaron"))
        for batch in batches.values():
            db.update_prices_batch(batch)
        status["dump_v6"] = True
    except Exception as exc:
        bot_logger.error(f"Error loading V6 dump: {exc}")

    return status
```

- [ ] **Step 4: Run daily dump tests**

Run:

```bash
python -m pytest tests/test_daily_dump.py -q
```

Expected:

```text
all daily dump tests pass
```

### Task 4: Centralize DB Reads And Freshness

**Files:**
- Create: `tests/test_db_manager.py`
- Modify: `app/database/db_manager.py`
- Modify: `app/core/probability.py`
- Modify: `app/core/contracts.py`

- [ ] **Step 1: Write DB tests**

Create `tests/test_db_manager.py`:

```python
from app.database.db_manager import DBManager


def test_update_and_get_all_price_records(tmp_path):
    db = DBManager(str(tmp_path / "test.db"))
    db.update_prices_batch(
        [
            ("A", 1.0, "steam"),
            ("A", 2.0, "csfloat"),
        ]
    )

    records = db.get_all_price_records()

    assert len(records) == 2
    assert records[0].keys() >= {"market_hash_name", "price", "source", "updated_at"}


def test_get_price_map_groups_by_item(tmp_path):
    db = DBManager(str(tmp_path / "test.db"))
    db.update_prices_batch([("A", 1.0, "steam"), ("A", 2.0, "csfloat")])

    price_map = db.get_price_map()

    assert price_map["A"]["steam"]["price"] == 1.0
    assert price_map["A"]["csfloat"]["price"] == 2.0
```

- [ ] **Step 2: Run DB tests and verify failure**

Run:

```bash
python -m pytest tests/test_db_manager.py -q
```

Expected:
- Fails because `get_all_price_records()` and `get_price_map()` do not exist.

- [ ] **Step 3: Add bulk read methods**

Add to `app/database/db_manager.py`:

```python
def get_all_price_records(self):
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT market_hash_name, price, source, updated_at FROM prices")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_price_map(self):
    price_map = {}
    for row in self.get_all_price_records():
        price_map.setdefault(row["market_hash_name"], {})[row["source"]] = {
            "price": row["price"],
            "updated_at": row["updated_at"],
        }
    return price_map
```

- [ ] **Step 4: Run DB tests**

Run:

```bash
python -m pytest tests/test_db_manager.py -q
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Remove global DB dependency from probability**

Change `simulate_contract_probabilities(inputs_data)` to accept `db_path=None`:

```python
def simulate_contract_probabilities(inputs_data, db_path=None):
    if len(inputs_data) != 10:
        raise ValueError("A trade-up contract requires exactly 10 inputs.")
    rarities = {inp["rarity"] for inp in inputs_data}
    if len(rarities) != 1:
        raise ValueError("All contract inputs must have the same rarity.")

    conn = sqlite3.connect(db_path or DB_PATH)
```

Update `ContractEngine.calculate_contract_profitability()` to call:

```python
outcomes = probability.simulate_contract_probabilities(inputs, db_path=self.db.db_path)
```

### Task 5: Filter False Arbitrage

**Files:**
- Modify: `app/core/arbitrage.py`
- Modify: `tests/test_arbitrage.py`
- Modify: `app/main.py`

- [ ] **Step 1: Add stale/untrusted source tests**

Extend `tests/test_arbitrage.py`:

```python
def test_arbitrage_ignores_untrusted_historical_sources():
    mock_db = MagicMock()
    mock_db.get_all_price_records.return_value = [
        {
            "market_hash_name": "Sticker | Titan (Holo) | Katowice 2014",
            "price": 91.98,
            "source": "csgobackpack",
            "updated_at": "2026-02-11 11:14:00",
        },
        {
            "market_hash_name": "Sticker | Titan (Holo) | Katowice 2014",
            "price": 143000.0,
            "source": "dump_buff",
            "updated_at": "2026-06-02 10:00:00",
        },
    ]

    opps = find_arbitrage_opportunities(
        rmb_to_usd=0.14,
        db_manager=mock_db,
        trusted_sources={"steam", "csfloat", "buff", "dump_buff"},
    )

    assert opps == []
```

- [ ] **Step 2: Run arbitrage tests and verify failure**

Run:

```bash
python -m pytest tests/test_arbitrage.py -q
```

Expected:
- Fails because `trusted_sources` is not supported and old code uses `get_all_prices()`.

- [ ] **Step 3: Implement trusted source and min ROI filtering**

Update function signature:

```python
def find_arbitrage_opportunities(
    rmb_to_usd=0.14,
    db_manager=None,
    min_roi=0.0,
    trusted_sources=None,
):
```

Use `get_all_price_records()` when present:

```python
records = db_manager.get_all_price_records()
if trusted_sources is None:
    trusted_sources = {
        "buff",
        "dump_buff",
        "steam",
        "dump_steam",
        "csfloat",
        "skinport",
        "dump_skinport",
        "skinbaron",
        "dump_skinbaron",
    }
records = [row for row in records if row["source"] in trusted_sources]
```

After calculating ROI:

```python
if roi >= min_roi:
    opportunities.append(
        {
            "name": name,
            "buy_source": b_source,
            "sell_source": s_source,
            "buy_price": b_price,
            "sell_price_net": s_net,
            "profit": profit,
            "roi": roi,
        }
    )
```

- [ ] **Step 4: Use `min_roi` from config**

In `app/main.py`, change:

```python
opps = arbitrage.find_arbitrage_opportunities(
    rmb_to_usd=rmb_to_usd,
    min_roi=config.min_roi,
)
```

- [ ] **Step 5: Run arbitrage and full tests**

Run:

```bash
python -m pytest tests/test_arbitrage.py -q
python -m pytest -q
```

Expected:

```text
all tests pass
```

### Task 6: Optimize And Correct Contract Engine

**Files:**
- Modify: `app/core/contracts.py`
- Modify: `tests/test_contracts.py`

- [ ] **Step 1: Add tests for dump sell fallback and duplicate-free recipes**

Extend `tests/test_contracts.py`:

```python
def test_get_lowest_price_uses_dump_fallback():
    db_manager = MagicMock()
    db_manager.get_price.side_effect = lambda name, source: {
        ("AK-47 | Slate (Field-Tested)", "dump_steam"): 2.0,
        ("AK-47 | Slate (Field-Tested)", "dump_buff"): 10.0,
    }.get((name, source))

    engine = ContractEngine(db_manager)

    assert engine.get_lowest_price("AK-47 | Slate", "Field-Tested") == pytest.approx(1.40)
```

- [ ] **Step 2: Run contract tests**

Run:

```bash
python -m pytest tests/test_contracts.py -q
```

Expected:
- Existing tests pass.
- New tests expose missing output dump fallback during the contract implementation task.

- [ ] **Step 3: Build a price index once**

In `ContractEngine.__init__`:

```python
self.price_map = self.db.get_price_map() if hasattr(self.db, "get_price_map") else None
```

Add helper:

```python
def _lookup_price(self, market_hash_name, source):
    if self.price_map is not None:
        source_data = self.price_map.get(market_hash_name, {}).get(source)
        return source_data["price"] if source_data else None
    return self.db.get_price(market_hash_name, source)
```

Use `_lookup_price()` instead of `self.db.get_price()` in all contract price reads.

- [ ] **Step 4: Add dump fallback for outcome sell prices**

Change outcome sell lookup:

```python
for source, fee in self.MARKET_FEES.items():
    p_sell = self._lookup_price(outcome_hash_name, source)
    if p_sell is None:
        p_sell = self._lookup_price(outcome_hash_name, f"dump_{source}")
```

- [ ] **Step 5: Remove duplicate 10x evaluations**

In `hunt_contracts()`, handle `10x` outside the filler loop:

```python
for target in targets:
    self._evaluate_combo(results, target, None, 10, 0, min_roi)
    for filler in fillers:
        if target["collection"] == filler["collection"]:
            continue
        self._evaluate_combo(results, target, filler, 9, 1, min_roi)
        self._evaluate_combo(results, target, filler, 5, 5, min_roi)
```

Make each result include:

```python
report["inputs"] = {
    "target": target["name"],
    "filler": filler["name"] if filler else None,
    "target_count": n_t,
    "filler_count": n_f,
    "input_float": input_float,
}
```

- [ ] **Step 6: Run a contract performance smoke**

Run:

```bash
python -c "from app.core.config import load_settings; from app.core.contracts import ContractEngine; from app.database.db_manager import DBManager; import time; c=load_settings('config.json'); t=time.perf_counter(); r=ContractEngine(DBManager(), c.rmb_to_usd).hunt_contracts(c.min_roi, c.max_budget); print(len(r), round(time.perf_counter()-t, 2))"
```

Expected:
- Finishes under 30 seconds on the current DB.

### Task 7: Make Buff And Steam Failures Visible

**Files:**
- Modify: `app/scrapers/buff/index.js`
- Modify: `app/scrapers/steam.py`
- Modify: `app/main.py`

- [ ] **Step 1: Make Buff exit nonzero on critical failure**

Change catch block in `app/scrapers/buff/index.js`:

```javascript
    } catch (error) {
        console.error(`[Buff] Critical failure: ${error.message}`);
        process.exitCode = 1;
    } finally {
```

Change response wait to capture non-200:

```javascript
const responsePromise = page.waitForResponse(response =>
    response.url().includes('/api/market/goods')
);
```

After `const response = await responsePromise;`:

```javascript
if (response.status() !== 200) {
    throw new Error(`Buff HTTP ${response.status()}`);
}
```

- [ ] **Step 2: Make Steam retry transient exceptions**

In `app/scrapers/steam.py`, move exception handling inside the retry loop:

```python
        except Exception as e:
            retry_count += 1
            if retry_count > max_retries:
                bot_logger.error(f"Error fetching Steam prices after retries: {e}")
                return False
            wait_time = 2**retry_count * 10
            bot_logger.warning(f"Steam request failed. Retrying in {wait_time}s: {e}")
            time.sleep(wait_time)
```

- [ ] **Step 3: Make `main.py` block analysis when all scrapers fail**

After `run_scrapers(config)`, return a status dict:

```python
scrape_status = run_scrapers(config)
if scrape_status and not any(scrape_status.values()):
    raise RuntimeError("All scrapers failed; refusing to analyze stale data.")
```

### Task 8: Make Continuous Loop Verify Actual Opportunities

**Files:**
- Modify: `app/core/intelligence_loop.py`
- Modify: `app/scrapers/csfloat.py`
- Create: `tests/test_intelligence_loop.py`

- [ ] **Step 1: Add loop test with fake opportunity names**

Create `tests/test_intelligence_loop.py`:

```python
from app.core.config import Settings
from app.core import intelligence_loop


def test_loop_passes_batch_names_to_live_verification(monkeypatch):
    seen = []

    monkeypatch.setattr(
        intelligence_loop.arbitrage,
        "find_arbitrage_opportunities",
        lambda rmb_to_usd: [{"name": "AK-47 | Slate (Field-Tested)", "profit": 1}],
    )
    monkeypatch.setattr(
        intelligence_loop.csfloat,
        "fetch_csfloat_prices",
        lambda limit, settings, market_hash_names=None: seen.extend(market_hash_names) or True,
    )
    monkeypatch.setattr(intelligence_loop.steam, "fetch_steam_prices", lambda limit: True)
    monkeypatch.setattr(intelligence_loop.daily_dump, "fetch_daily_dumps", lambda: {"dump_buff": True})
    monkeypatch.setattr(intelligence_loop.time, "sleep", lambda _: None)

    settings = Settings(buff_session="", batch_size=1, batch_sleep=0)
    intelligence_loop.run_continuous_loop(settings, max_cycles=1)

    assert seen == ["AK-47 | Slate (Field-Tested)"]
```

- [ ] **Step 2: Add `max_cycles` to loop**

Change signature:

```python
def run_continuous_loop(config: Settings, max_cycles=None):
```

At the end of each cycle:

```python
cycle_count += 1
if max_cycles is not None and cycle_count >= max_cycles:
    return
```

- [ ] **Step 3: Pass market names to CSFloat**

Add optional parameter to `fetch_csfloat_prices`:

```python
def fetch_csfloat_prices(limit=50, settings=None, db_manager=None, scraper=None, market_hash_names=None):
```

When `market_hash_names` is provided, call CSFloat once per name with `market_hash_name` query parameter and `type=buy_now`.

- [ ] **Step 4: Run loop tests**

Run:

```bash
python -m pytest tests/test_intelligence_loop.py -q
```

Expected:

```text
1 passed
```

### Task 9: Documentation And Report Truthfulness

**Files:**
- Modify: `README.md`
- Modify: `docs/design_spec.md`
- Create or modify: `docs/superpowers/specs/2026-06-02-operational-status.md`

- [ ] **Step 1: Add operational status doc**

Create `docs/superpowers/specs/2026-06-02-operational-status.md`:

```markdown
# Operational Status - 2026-06-02

## Working
- Unit tests for core math/arbitrage basics pass.
- DB schema supports multi-source prices.

## Fixed In Stabilization Plan
- CSFloat parser supports `data/cursor`.
- Scrapers return observable status.
- Arbitraje filters untrusted/stale sources.

## Still Requires Live Validation
- Buff session validity.
- CSGOTrader daily dump availability.
- Steam rate limits.
```

- [ ] **Step 2: Update README claims**

Replace claims of full Skinport/Skinbaron API support with:

```markdown
Skinport and Skinbaron are currently consumed through daily dump data when available. Dedicated authenticated scrapers are not implemented yet.
```

Add:

```markdown
The bot refuses or marks reports as stale when all live scrapers fail or when source data exceeds the configured freshness window.
```

### Task 10: Final Verification

**Files:**
- All modified files.

- [ ] **Step 1: Run Python tests**

Run:

```bash
python -m pytest -q
```

Expected:

```text
all tests pass
```

- [ ] **Step 2: Run CSFloat live smoke**

Run:

```bash
python -c "from app.scrapers.csfloat import fetch_csfloat_prices; print(fetch_csfloat_prices(1))"
```

Expected:

```text
True
```

- [ ] **Step 3: Run analysis smoke without report overwrite**

Run:

```bash
python -c "from app.core.config import load_settings; from app.core import arbitrage; c=load_settings('config.json'); r=arbitrage.find_arbitrage_opportunities(c.rmb_to_usd, min_roi=c.min_roi); print(len(r)); print(r[0] if r else None)"
```

Expected:
- No `csgobackpack` stale top result.
- Count is plausible and filtered.

- [ ] **Step 4: Run contract performance smoke**

Run:

```bash
python -c "from app.core.config import load_settings; from app.core.contracts import ContractEngine; from app.database.db_manager import DBManager; import time; c=load_settings('config.json'); t=time.perf_counter(); r=ContractEngine(DBManager(), c.rmb_to_usd).hunt_contracts(c.min_roi, c.max_budget); print(len(r), round(time.perf_counter()-t, 2))"
```

Expected:
- Finishes under 30 seconds.
- Results include input recipe fields.

- [ ] **Step 5: Check Git state**

Run:

```bash
git status --short
```

Expected:
- Only intentional code/docs/test changes are present.
- No `config.json`, logs, `.venv`, or `node_modules` are staged.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-02-cs2-trade-bot-stabilization.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, faster iteration.
2. **Inline Execution** - execute tasks in this session using `superpowers:executing-plans`, with checkpoints.
