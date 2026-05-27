# CS2 Trade-Up Contract Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a centralized `ContractEngine` in `app/core/contracts.py` that handles price fetching, profitability analysis, and contract hunting.

**Architecture:** A modular class-based approach that coordinates between the database and core math/probability engines.

**Tech Stack:** Python, SQLite3.

---

### Task 1: Setup ContractEngine and get_lowest_price

**Files:**
- Create: `app/core/contracts.py`
- Create: `tests/test_contracts.py`

- [ ] **Step 1: Write the failing test for get_lowest_price**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_contracts.py -v`
Expected: FAIL (Module not found)

- [ ] **Step 3: Implement ContractEngine skeleton and get_lowest_price**

```python
class ContractEngine:
    BUFF_MULTIPLIER = 0.14
    MARKET_FEES = {
        'steam': 0.15,
        'csfloat': 0.02,
        'buff': 0.025
    }

    def __init__(self, db_manager):
        self.db = db_manager

    def get_lowest_price(self, skin_name, wear):
        hash_name = f"{skin_name} ({wear})"
        prices = []
        
        for source in ['steam', 'csfloat', 'buff']:
            p = self.db.get_price(hash_name, source)
            if p is not None:
                if source == 'buff':
                    p *= self.BUFF_MULTIPLIER
                prices.append(p)
        
        return min(prices) if prices else None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_contracts.py -v`

- [ ] **Step 5: Commit**

```bash
git add app/core/contracts.py tests/test_contracts.py
git commit -m "feat: add ContractEngine and get_lowest_price"
```

---

### Task 2: Implement calculate_contract_profitability

**Files:**
- Modify: `app/core/contracts.py`
- Modify: `tests/test_contracts.py`

- [ ] **Step 1: Write failing test for profitability**

```python
def test_calculate_contract_profitability():
    db_manager = MagicMock()
    # Mock prices for inputs and outcomes...
    # (Simplified mock for brevity in plan, but implementation needs full data)
    db_manager.get_price.return_value = 1.0 
    
    engine = ContractEngine(db_manager)
    inputs = [{'name': 'Skin A', 'collection': 'Col A', 'rarity': 'Mil-Spec Grade', 'float': 0.1, 'min_float': 0.0, 'max_float': 1.0}] * 10
    
    report = engine.calculate_contract_profitability(inputs)
    assert 'roi' in report
    assert 'profit' in report
    assert 'cost' in report
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_contracts.py -v`

- [ ] **Step 3: Implement calculate_contract_profitability**

```python
from app.core import math_engine, probability

# Inside ContractEngine class:
    def calculate_contract_profitability(self, inputs):
        # 1. Calculate Cost
        total_cost = 0
        for inp in inputs:
            wear = math_engine.get_wear_name(inp['float'])
            p = self.get_lowest_price(inp['name'], wear)
            if p is None:
                return {"error": f"Missing price for {inp['name']} ({wear})"}
            total_cost += p

        # 2. Simulate Outcomes
        outcomes = probability.simulate_contract_probabilities(inputs)
        
        expected_revenue = 0
        detailed_outcomes = []
        
        for outcome in outcomes:
            prob = outcome['chance_percent'] / 100.0
            out_float = math_engine.calculate_outcome_float(inputs, outcome['min_float'], outcome['max_float'])
            out_wear = math_engine.get_wear_name(out_float)
            
            # Highest Net Sell Price
            max_net = 0
            best_source = None
            sell_prices = {}
            
            for source, fee in self.MARKET_FEES.items():
                p_sell = self.db.get_price(f"{outcome['name']} ({out_wear})", source)
                if p_sell:
                    if source == 'buff': p_sell *= self.BUFF_MULTIPLIER
                    net = p_sell * (1 - fee)
                    sell_prices[source] = p_sell
                    if net > max_net:
                        max_net = net
                        best_source = source
            
            expected_revenue += prob * max_net
            detailed_outcomes.append({
                "name": outcome['name'],
                "wear": out_wear,
                "float": out_float,
                "probability": outcome['chance_percent'],
                "max_net_revenue": max_net,
                "best_market": best_source
            })

        profit = expected_revenue - total_cost
        roi = (profit / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "cost": total_cost,
            "revenue": expected_revenue,
            "profit": profit,
            "roi": roi,
            "outcomes": detailed_outcomes
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_contracts.py -v`

- [ ] **Step 5: Commit**

```bash
git add app/core/contracts.py tests/test_contracts.py
git commit -m "feat: implement calculate_contract_profitability"
```

---

### Task 3: Implement hunt_contracts

**Files:**
- Modify: `app/core/contracts.py`
- Modify: `tests/test_contracts.py`

- [ ] **Step 1: Write failing test for hunt_contracts**

```python
def test_hunt_contracts():
    db_manager = MagicMock()
    # Mock DB queries for skins...
    engine = ContractEngine(db_manager)
    results = engine.hunt_contracts(min_roi=10, max_budget=20)
    assert isinstance(results, list)
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement hunt_contracts**

```python
# Inside ContractEngine class:
    def hunt_contracts(self, min_roi=10.0, max_budget=25.0):
        # This requires a more complex DB query helper
        # For simplicity in this step, I'll use a cursor-based approach
        conn = self.db.get_connection() # Assume DBManager has this or similar
        cursor = conn.cursor()
        
        # 1. Get all skins
        cursor.execute("SELECT name, collection, rarity, min_float, max_float FROM skins")
        all_skins = [
            {'name': r[0], 'collection': r[1], 'rarity': r[2], 'min_float': r[3], 'max_float': r[4]}
            for r in cursor.fetchall()
        ]
        
        # Group by rarity
        by_rarity = {}
        for s in all_skins:
            if s['rarity'] not in by_rarity: by_rarity[s['rarity']] = []
            by_rarity[s['rarity']].append(s)
            
        results = []
        rarity_tiers = ["Industrial Grade", "Mil-Spec Grade", "Restricted", "Classified"]
        
        for rarity in rarity_tiers:
            skins = by_rarity.get(rarity, [])
            if len(skins) < 2: continue
            
            # Sort by price (approx FT)
            for s in skins:
                s['price'] = self.get_lowest_price(s['name'], "Field-Tested") or 9999
            
            skins.sort(key=lambda x: x['price'])
            fillers = skins[:5]
            targets = [s for s in skins if s['price'] <= max_budget]
            
            for target in targets:
                for filler in fillers:
                    if target['collection'] == filler['collection']: continue
                    
                    combos = [(10, 0), (9, 1), (5, 5)]
                    for n_t, n_f in combos:
                        inputs = []
                        for _ in range(n_t): 
                            t_copy = target.copy()
                            t_copy['float'] = 0.08
                            inputs.append(t_copy)
                        for _ in range(n_f):
                            f_copy = filler.copy()
                            f_copy['float'] = 0.08
                            inputs.append(f_copy)
                            
                        report = self.calculate_contract_profitability(inputs)
                        if "error" not in report and report['roi'] >= min_roi:
                            results.append(report)
        return results
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add app/core/contracts.py tests/test_contracts.py
git commit -m "feat: implement hunt_contracts"
```
