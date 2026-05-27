# CS2 Robust Intelligence Bot v2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a high-volume, low-risk market intelligence system using daily data dumps and smart live verification loops.

**Architecture:** 
1. **Data Dump Layer:** Bulk loader for daily pricing JSONs.
2. **Smart Scraper Layer:** API Key support for CSFloat and enhanced rate-limiting for Steam/Buff.
3. **Continuous Intelligence Loop:** Orchestrator that iterates through unverified opportunities in safe batches.

**Tech Stack:** Python, Node.js + Playwright, SQLite.

---

### Task 1: Daily Dump Integration

**Files:**
- Create: `app/scrapers/daily_dump.py`
- Modify: `app/database/db_manager.py` (Add bulk sources support)

- [ ] **Step 1: Update DBManager for Dump Sources**
Add "dump_buff", "dump_steam", "dump_skinport", "dump_skinbaron" to the source handling.

- [ ] **Step 2: Implement Daily Dump Scraper**
Create `app/scrapers/daily_dump.py` to download JSONs from `prices.csgotrader.app` and populate the DB.

- [ ] **Step 3: Commit**
```bash
git add app/
git commit -m "feat: add daily dump integration"
```

### Task 2: CSFloat API Key & Steam Anti-Ban Enhancements

**Files:**
- Modify: `app/scrapers/csfloat.py` (Add Authorization header)
- Modify: `app/scrapers/steam.py` (Add jitter and tighter limits)
- Modify: `config.json` (Add csfloat_api_key field)

- [ ] **Step 1: Add CSFloat API Key support**
Update `csfloat.py` to use `headers={"Authorization": f"Bearer {api_key}"}`.

- [ ] **Step 2: Implement Anti-Ban Jitter**
Add random sleeps between Steam/Buff requests.

- [ ] **Step 3: Commit**
```bash
git add app/scrapers/ config.json
git commit -m "feat: enhance scrapers with API Key and anti-ban jitter"
```

### Task 3: Continuous Intelligence Loop (Orchestrator)

**Files:**
- Modify: `app/main.py`
- Create: `app/core/intelligence_loop.py`

- [ ] **Step 1: Create Intelligence Loop Controller**
Implement the batch processing logic (verify 50, sleep, verify next 50).

- [ ] **Step 2: Update Main Orchestrator**
Add a `--loop` flag to run the bot in continuous mode.

- [ ] **Step 3: Commit**
```bash
git add app/
git commit -m "feat: implement continuous intelligence loop"
```

### Task 4: Multi-Market Arbitrage & Improved Contracts

**Files:**
- Modify: `app/core/arbitrage.py` (Add Skinport/Baron)
- Modify: `app/core/contracts.py` (Optimize for Dump-based pre-filtering)

- [ ] **Step 1: Enhance Arbitrage Engine**
Add logic to compare against Skinport/Baron net prices.

- [ ] **Step 2: Implement "Smart-Verify" in Contracts**
Update `hunt_contracts` to use Dump data for initial scan and then trigger Live verification for top candidates.

- [ ] **Step 3: Commit**
```bash
git add app/core/
git commit -m "feat: enhance analysis engines with multi-market and smart-verify"
```

### Task 5: Documentation & README

**Files:**
- Modify: `README.md`
- Modify: `config.example.json`

- [ ] **Step 1: Update Documentation**
Document the new `--loop` mode, the daily dump feature, and the CSFloat API key configuration.

- [ ] **Step 2: Commit**
```bash
git add README.md config.example.json
git commit -m "docs: update README with new features and usage"
```
