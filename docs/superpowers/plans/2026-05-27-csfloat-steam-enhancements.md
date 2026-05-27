# CSFloat API Key & Anti-Ban Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance scrapers with CSFloat API Key support and random delays for Steam and Buff.

**Architecture:** Update configuration, modify scraper request logic to include headers and delays.

**Tech Stack:** Python (cloudscraper), Node.js (Playwright).

---

### Task 1: Update Configuration

**Files:**
- Modify: `config.json`

- [ ] **Step 1: Add `csfloat_api_key` to `config.json`**

```json
{
    "min_roi": 15.0,
    "max_budget": 50.0,
    "buff_session": "...",
    "steam_limit": 50,
    "csfloat_limit": 50,
    "rmb_to_usd": 0.14,
    "csfloat_api_key": ""
}
```

---

### Task 2: Enhance CSFloat Scraper

**Files:**
- Modify: `app/scrapers/csfloat.py`

- [ ] **Step 1: Update `fetch_csfloat_prices` to load and use API Key**

```python
import os
import json
import cloudscraper
from app.database.db_manager import DBManager

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def fetch_csfloat_prices(limit=100):
    # ...
    config = load_config()
    api_key = config.get("csfloat_api_key")
    headers = {}
    if api_key:
        headers["Authorization"] = api_key
    
    # ...
    response = scraper.get(url, headers=headers, timeout=30)
    # ...
```

---

### Task 3: Enhance Steam Scraper with Jitter

**Files:**
- Modify: `app/scrapers/steam.py`

- [ ] **Step 1: Add `import random` and `time.sleep` jitter**

```python
import time
import random
# ...

def fetch_steam_prices(limit=100):
    # ...
    print(f"🚀 Fetching {limit} items from Steam...")
    
    # Add initial jitter
    time.sleep(random.uniform(1.0, 3.0))
    
    # ...
    while retry_count <= max_retries:
        # Add jitter before each request
        if retry_count > 0:
            time.sleep(random.uniform(1.0, 3.0))
        # ...
```

---

### Task 4: Enhance Buff Scraper with Jitter

**Files:**
- Modify: `app/scrapers/buff/index.js`

- [ ] **Step 1: Add `page.waitForTimeout` jitter**

```javascript
// ...
        // Intercept the API response to get the raw JSON data
        const responsePromise = page.waitForResponse(response => 
            response.url().includes('/api/market/goods') && response.status() === 200
        );

        // Add random delay (1-3 seconds)
        await page.waitForTimeout(Math.random() * 2000 + 1000);

        await page.goto(url);
// ...
```

---

### Task 5: Verify Changes

- [ ] **Step 1: Run scrapers to ensure they still work**

Run: `python app/main.py --scrape`
Expected: Scrapers run successfully (even if they fail due to external factors like session expiry, they should not crash due to code errors).
