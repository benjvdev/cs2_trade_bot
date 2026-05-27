# Design Spec: CS2 Trade Bot Professionalization (Surgical Clean & Test)

**Date:** 2026-05-27
**Status:** Approved
**Approach:** Surgical Clean & Test (Enfoque 1)

## 1. Goal
Professionalize the `cs2_trade_bot` project by establishing a clean directory structure, implementing robust configuration validation, enforcing type safety, and creating a reliable testing suite.

## 2. Architecture & Components

### 2.1 Directory Cleanup & Reorganization
The project root will be decluttered to follow professional standards.
- **Root:** Only essential configuration (`config.json`, `.gitignore`), meta-files (`README.md`, `requirements.txt`), and the entry point (`app/main.py`).
- **New Folders:**
    - `scripts/legacy/`: Contains older standalone versions or research scripts (`db_builder.py`, `price_fetcher.py`, `hunter.py`, `profit_engine.py`, `contract_simulator.py`).
    - `logs/`: Centralized location for rotating log files.
- **Deletion:** Removal of temporary verification scripts (`check_p90.py`, `check_prices.py`, `check_sources.py`, `manual_tester.py`, `manual_verify.py`).
- **Reports:** Move `hunter_results.txt` to the `reports/` directory.

### 2.2 Configuration & Robustness
Transition from raw JSON loading to a validated configuration model.
- **Config Model:** Implement `app/core/config.py` using **Pydantic**.
    - Define a `Settings` class to validate types (e.g., `min_roi` as float, `buff_session` as string).
    - Provide default values and environment variable override support.
- **Type Safety:** Add PEP 484 Type Hints across all files in `app/core/` and `app/scrapers/`.
- **Logging:** Implement a standard logging configuration in `app/utils/logger.py` with `RotatingFileHandler` for the `logs/` directory and colored output for the console.

### 2.3 Testing Strategy
Implementation of a robust verification layer using `pytest`.
- **Unit Tests:**
    - `tests/test_math_engine.py`: Verify IEEE 754 float precision in `calculate_outcome_float`.
    - `tests/test_probability.py`: Validate contract outcome distributions.
    - `tests/test_arbitrage_logic.py`: Verify net profit and ROI calculations including multi-market fees.
- **Integration Tests:**
    - `tests/test_db_manager.py`: Test schema creation, batch updates, and retrieval using an in-memory SQLite database.
- **Mocking:** Use `unittest.mock` to simulate API responses for scrapers during testing to avoid rate limits and network dependency.

## 3. Success Criteria
1. The bot starts only if `config.json` passes validation.
2. The project root is free of utility/check scripts.
3. `pytest` executes successfully with >80% coverage on core logic.
4. All logs are directed to `logs/bot.log` while maintaining informative console output.
