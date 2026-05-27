# Multi-Market Arbitrage & Improved Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance the arbitrage engine with new markets (Skinport, Skinbaron) and fee logic, and optimize the contract hunter using dump data as a primary filter.

**Architecture:** 
- Arbitrage: Consolidate prices from all sources, prioritizing live data over dump data, and apply source-specific fees.
- Contracts: Use dump data for initial ROI calculations to pre-filter candidates before live verification.

**Tech Stack:** Python, SQLite

---

### Task 1: Enhance Arbitrage Engine Fee Logic & Data Precedence

**Files:**
- Modify: `app/core/arbitrage.py`

- [ ] **Step 1: Define fees and mapping**

Update `find_arbitrage_opportunities` to include a comprehensive fee mapping and data precedence logic.

```python
def find_arbitrage_opportunities(rmb_to_usd=0.14):
    db = DBManager()
    try:
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT market_hash_name, price, source FROM prices')
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"Database error in arbitrage engine: {e}")
        return []

    FEES = {
        'buff': 0.025,
        'dump_buff': 0.025,
        'steam': 0.15,
        'dump_steam': 0.15,
        'csfloat': 0.02,
        'skinport': 0.12,
        'dump_skinport': 0.12,
        'skinbaron': 0.15,
        'dump_skinbaron': 0.15
    }

    # Group prices by item and market (consolidating dump/live)
    items = {}
    for name, price, source in rows:
        if name not in items:
            items[name] = {}
        
        # Determine base market name (e.g., 'dump_steam' -> 'steam')
        market_base = source.replace('dump_', '')
        
        # Prioritize live over dump: 
        # If we don't have this market yet, OR if this is a live source (doesn't start with dump_)
        if market_base not in items[name] or not source.startswith('dump_'):
            items[name][market_base] = (price, source)
        
    opportunities = []
    for name, markets in items.items():
        if len(markets) < 2:
            continue
            
        buy_costs = {}
        net_sales = {}

        for market_base, (price, source) in markets.items():
            fee = FEES.get(source, 0)
            
            # Convert to USD
            usd_price = price
            if market_base == 'buff':
                usd_price = price * rmb_to_usd
            
            buy_costs[source] = usd_price
            net_sales[source] = usd_price * (1 - fee)

        for b_source, b_price in buy_costs.items():
            for s_source, s_net in net_sales.items():
                if b_source == s_source: continue
                if b_price < s_net:
                    profit = s_net - b_price
                    roi = (profit / b_price) * 100
                    opportunities.append({
                        'name': name,
                        'buy_source': b_source,
                        'sell_source': s_source,
                        'buy_price': b_price,
                        'sell_price_net': s_net,
                        'profit': profit,
                        'roi': roi
                    })
            
    return sorted(opportunities, key=lambda x: x['profit'], reverse=True)
```

- [ ] **Step 2: Commit**

```bash
git add app/core/arbitrage.py
git commit -m "feat: improve arbitrage engine with multi-market support and live data priority"
```

---

### Task 2: Optimize Contract Engine with Smart-Verify

**Files:**
- Modify: `app/core/contracts.py`

- [ ] **Step 1: Update FEES mapping**

Update `ContractEngine.MARKET_FEES` to match the arbitrage engine.

```python
class ContractEngine:
    MARKET_FEES = {
        'steam': 0.15,
        'csfloat': 0.02,
        'buff': 0.025,
        'skinport': 0.12,
        'skinbaron': 0.15
    }
```

- [ ] **Step 2: Implement Smart-Verify in hunt_contracts**

Modify `hunt_contracts` to pre-filter and calculate ROI using dump data.

```python
    def hunt_contracts(self, min_roi=10.0, max_budget=25.0):
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # 1. Load all dump prices for pre-filtering
        cursor.execute("SELECT market_hash_name, price, source FROM prices WHERE source LIKE 'dump_%'")
        dump_prices = {}
        for name, price, source in cursor.fetchall():
            market_base = source.replace('dump_', '')
            if name not in dump_prices: dump_prices[name] = {}
            dump_prices[name][market_base] = price

        cursor.execute("SELECT name, collection, rarity, min_float, max_float FROM skins")
        all_skins = [
            {'name': r[0], 'collection': r[1], 'rarity': r[2], 'min_float': r[3], 'max_float': r[4]}
            for r in cursor.fetchall()
        ]
        
        by_rarity = {}
        for s in all_skins:
            if s['rarity'] not in by_rarity: by_rarity[s['rarity']] = []
            by_rarity[s['rarity']].append(s)
            
        results = []
        rarity_tiers = ["Industrial Grade", "Mil-Spec Grade", "Restricted", "Classified"]
        
        for rarity in rarity_tiers:
            skins = by_rarity.get(rarity, [])
            if len(skins) < 2: continue
            
            # Pre-filter skins using dump data
            valid_skins = []
            for s in skins:
                # Try to get lowest dump price
                hash_name = f"{s['name']} (Field-Tested)"
                p_list = []
                if hash_name in dump_prices:
                    for m, p in dump_prices[hash_name].items():
                        if m == 'buff': p *= self.rmb_to_usd
                        p_list.append(p)
                
                if p_list:
                    p = min(p_list)
                    if p <= max_budget:
                        s['price'] = p
                        valid_skins.append(s)
            
            valid_skins.sort(key=lambda x: x['price'])
            if len(valid_skins) < 10: continue # Need enough skins for combos

            # Optimization: only check cheapest skins as inputs
            inputs_pool = valid_skins[:20]
            
            for target in inputs_pool:
                # ... (rest of the logic for combinations)
```

- [ ] **Step 3: Modify calculate_contract_profitability to handle dump data**

Update `get_lowest_price` to check for dump data if live data is missing.

```python
    def get_lowest_price(self, skin_name, wear):
        hash_name = f"{skin_name} ({wear})"
        prices = []
        
        sources = ['steam', 'csfloat', 'buff', 'skinport', 'skinbaron']
        for s in sources:
            # Check live
            p = self.db.get_price(hash_name, s)
            if p is None:
                # Check dump
                p = self.db.get_price(hash_name, f"dump_{s}")
            
            if p is not None:
                if s == 'buff': p *= self.rmb_to_usd
                prices.append(p)
        
        return min(prices) if prices else None
```

- [ ] **Step 4: Commit**

```bash
git add app/core/contracts.py
git commit -m "feat: implement smart-verify in contract engine using dump data"
```
