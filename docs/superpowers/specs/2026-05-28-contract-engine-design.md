# Design Spec: CS2 Trade-Up Contract Engine

## Overview
Refactor and centralize trade-up contract logic from `hunter.py` and `profit_engine.py` into a modern, modular `ContractEngine` class in `app/core/contracts.py`.

## Architecture
- **Location**: `app/core/contracts.py`
- **Class**: `ContractEngine`
- **Dependencies**:
    - `app.database.db_manager.DBManager`: For price and skin data.
    - `app.core.math_engine`: For float calculations and wear names.
    - `app.core.probability`: For outcome simulations.

## Constants
- `BUFF_MULTIPLIER = 0.14` (Conversion from Buff CNY to USD/Internal value)
- `MARKET_FEES`:
    - `steam`: 0.15 (15%)
    - `csfloat`: 0.02 (2%)
    - `buff`: 0.025 (2.5%)

## Detailed Design

### 1. `get_lowest_price(skin_name, wear)`
- **Purpose**: Find the cheapest buying option for a skin.
- **Inputs**: `skin_name` (str), `wear` (str).
- **Logic**:
    - Construct `market_hash_name` as `"{skin_name} ({wear})"`.
    - Fetch prices from `buff`, `steam`, `csfloat` using `DBManager`.
    - Apply `BUFF_MULTIPLIER` to `buff` prices.
    - Return the minimum of available prices. If no prices found, return `None`.

### 2. `calculate_contract_profitability(inputs)`
- **Purpose**: Calculate the expected value, profit, and ROI of a specific contract.
- **Inputs**: `inputs` (list of 10 dicts with `name`, `collection`, `rarity`, `float`, `min_float`, `max_float`).
- **Logic**:
    - Calculate total cost by summing `get_lowest_price` for each input skin.
    - Call `probability.simulate_contract_probabilities(inputs)` to get possible outcomes.
    - For each outcome:
        - Calculate `output_float` using `math_engine.calculate_outcome_float`.
        - Get `wear_name` using `math_engine.get_wear_name`.
        - Fetch sell prices from `buff`, `steam`, `csfloat`.
        - Calculate net revenue for each source: `price * (1 - fee)`.
        - Select `max_net_revenue` for this outcome.
        - Add `outcome_probability * max_net_revenue` to `total_expected_revenue`.
    - Calculate `profit = total_expected_revenue - total_cost`.
    - Calculate `roi = (profit / total_cost) * 100`.
    - Return a structured report including cost, revenue, profit, ROI, and detailed outcomes.

### 3. `hunt_contracts(min_roi, max_budget)`
- **Purpose**: Automatically discover profitable trade-up combinations.
- **Inputs**: `min_roi` (float), `max_budget` (float).
- **Logic**:
    - Fetch all skins from DB.
    - Group by rarity.
    - For each rarity tier (that has a next tier):
        - Identify "fillers" (top 5 cheapest skins).
        - Identify "targets" (skins within budget).
        - Test combinations:
            - 10x target skins.
            - 9x target + 1x filler.
            - 5x target + 5x filler.
        - Use a test float of `0.08` for all inputs.
        - Run `calculate_contract_profitability`.
        - If `roi >= min_roi`, add to results.
- **Output**: List of profitability reports for profitable contracts.

## Error Handling
- If a price is missing for an input skin, the contract is considered invalid (skip).
- If no outcomes are found for a rarity tier (e.g. Covert), skip.
- Handle database connection issues gracefully through `DBManager`.

## Testing Strategy
- **Unit Tests**:
    - Test `get_lowest_price` with mocked DB responses.
    - Test `calculate_contract_profitability` with known outcomes and prices.
- **Integration Tests**:
    - Test `hunt_contracts` against a test database.
