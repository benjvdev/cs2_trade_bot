# CS2 Trade & Arbitrage Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the existing codebase into a modular architecture and implement multi-market scraping (Buff, Steam, CSFloat) with arbitrage and enhanced contract hunting.

**Architecture:** Modular "Worker-Engine" pattern. Scrapers populate a multi-source SQLite database, and specialized engines (Arbitrage, Contracts) process this data to generate actionable reports.

**Tech Stack:** Python (Core/Scrapers), Node.js + Playwright (Buff Scraper), SQLite.

---

### Task 1: Project Restructuring

**Files:**
- Create: `app/__init__.py`, `app/core/__init__.py`, `app/database/__init__.py`, `app/scrapers/__init__.py`, `app/utils/__init__.py`
- Move: `math_engine.py` -> `app/core/math_engine.py`
- Move: `probability_engine.py` -> `app/core/probability.py`

- [ ] **Step 1: Create directory structure**
Run: `mkdir app/core, app/database, app/scrapers, app/utils, app/scrapers/buff, data, reports -Force` (PowerShell)

- [ ] **Step 2: Initialize packages**
Create empty `__init__.py` files in `app/`, `app/core/`, `app/database/`, `app/scrapers/`, `app/utils/`.

- [ ] **Step 3: Move core logic files**
Move `math_engine.py` to `app/core/math_engine.py` and `probability_engine.py` to `app/core/probability.py`. Update internal imports if necessary.

- [ ] **Step 4: Commit**
```bash
git add app/
git commit -m "refactor: setup project structure and move core engines"
```

### Task 2: Database Manager (Multi-source)

**Files:**
- Create: `app/database/db_manager.py`
- Modify: `app/database/db_manager.py` to handle `prices` table with `source` column.

- [ ] **Step 1: Implement Database Manager class**
Create `app/database/db_manager.py` with methods to initialize the DB and upsert prices for specific sources.

```python
import sqlite3
import os

class DBManager:
    def __init__(self, db_path="data/cs2_skins.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skins (
                id TEXT PRIMARY KEY, name TEXT, rarity TEXT, collection TEXT,
                min_float REAL, max_float REAL, image_url TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                market_hash_name TEXT, price REAL, source TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (market_hash_name, source)
            )
        ''')
        conn.commit()
        conn.close()

    def update_price(self, name, price, source):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO prices (market_hash_name, price, source, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (name, price, source))
        conn.commit()
        conn.close()
```

- [ ] **Step 2: Test DB Manager**
Create a test script to verify price insertion.

- [ ] **Step 3: Commit**
```bash
git add app/database/db_manager.py
git commit -m "feat: add multi-source database manager"
```

### Task 3: Steam & CSFloat Workers (Python)

**Files:**
- Create: `app/scrapers/steam.py`
- Create: `app/scrapers/csfloat.py`

- [ ] **Step 1: Implement Steam Bulk Scraper**
Use `requests` to fetch data from Steam Market search JSON.

- [ ] **Step 2: Implement CSFloat API Scraper**
Fetch current lowest prices from CSFloat Market API.

- [ ] **Step 3: Commit**
```bash
git add app/scrapers/
git commit -m "feat: add Steam and CSFloat workers"
```

### Task 4: Buff163 Worker (Node.js + Playwright)

**Files:**
- Create: `app/scrapers/buff/package.json`
- Create: `app/scrapers/buff/index.js`

- [ ] **Step 1: Setup Node.js project**
Initialize `package.json` in `app/scrapers/buff/` and install `playwright` and `sqlite3`.

- [ ] **Step 2: Implement Buff Scraper**
Write a script that uses Playwright to navigate Buff163 with provided cookies and extract prices to the SQLite DB.

- [ ] **Step 3: Commit**
```bash
git add app/scrapers/buff/
git commit -m "feat: add Buff163 browser-based worker"
```

### Task 5: Arbitrage & Contracts Engines

**Files:**
- Create: `app/core/arbitrage.py`
- Create: `app/core/contracts.py`

- [ ] **Step 1: Implement Arbitrage Logic**
Compare prices across sources in the DB, applying fees for each market.

- [ ] **Step 2: Implement Enhanced Contract Hunter**
Refactor existing `hunter.py` logic into `contracts.py` to support dynamic combinations and Buff-based input costs.

- [ ] **Step 3: Commit**
```bash
git add app/core/
git commit -m "feat: implement arbitrage and enhanced contract engines"
```

### Task 6: Main Entry & Reporting

**Files:**
- Create: `app/main.py`
- Create: `config.json`

- [ ] **Step 1: Create config.json**
Add user-configurable limits (min ROI, budget, etc.).

- [ ] **Step 2: Implement Main Orchestrator**
Create `app/main.py` to run scrapers (sequentially) and then trigger engine analysis and CSV report generation.

- [ ] **Step 3: Commit**
```bash
git add app/main.py config.json
git commit -m "feat: add main orchestrator and config"
```
