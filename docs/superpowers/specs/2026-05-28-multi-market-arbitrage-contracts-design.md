# Design Spec: Multi-Market Arbitrage & Improved Contracts

## Status: Approved

## 1. Overview
Enhance the arbitrage engine to support additional markets (Skinport, Skinbaron) with correct fee logic and implement "Smart-Verify" in the Contract Hunter to optimize data processing and API usage.

## 2. Goals
- Support `dump_skinport` (12% fee) and `dump_skinbaron` (15% fee).
- Implement tiered fee logic for all sources.
- Prioritize live data over dump data in arbitrage calculations.
- Optimize contract hunting by using dump data as a primary filter.

## 3. Architecture & Data Flow

### 3.1 Arbitrage Engine (`app/core/arbitrage.py`)
- **Consolidation Logic:** 
  1. Fetch all prices from the database.
  2. Group by `market_hash_name`.
  3. For each market (e.g., Steam), if `steam` (live) exists, use it; otherwise, use `dump_steam`.
- **Fee Structure:**
  - `buff`: 2.5%
  - `steam`: 15%
  - `csfloat`: 2%
  - `skinport`: 12%
  - `skinbaron`: 15%
- **Buy/Sell Logic:**
  - `buy_price`: The raw price from the source (converted to USD if necessary).
  - `sell_price_net`: `raw_price * (1 - fee)`.

### 3.2 Contract Engine (`app/core/contracts.py`)
- **Smart-Verify Logic:**
  - `hunt_contracts` will fetch all `dump_*` prices into memory.
  - Initial ROI calculations for recipes will use these dump prices.
  - Profitable recipes will be returned with a `needs_live_verification` flag.
- **Performance:** Pre-filtering skins using dump data to avoid iterating over skins with no available pricing.

## 4. Implementation Details

### 4.1 Arbitrage Source Mapping
```python
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
```

### 4.2 Data Precedence Logic
```python
# Pseudo-code
for name, price, source in rows:
    market_base = source.replace('dump_', '')
    if market_base not in items[name] or not source.startswith('dump_'):
        items[name][market_base] = (price, source)
```

## 5. Testing Strategy
- **Unit Tests:**
  - Test `find_arbitrage_opportunities` with mock data containing both live and dump sources.
  - Test `hunt_contracts` pre-filtering with dump data.
- **Verification:**
  - Check that ROI calculations correctly apply the 12% and 15% fees for Skinport and Skinbaron.
