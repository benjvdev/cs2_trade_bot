# Professional Logging System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement professional rotating logging system for CS2 Trade Bot to replace standard `print` statements.

**Architecture:** A centralized logger utility in `app/utils/logger.py` that configures a logger named "cs2_bot". It uses a `StreamHandler` for console output and a `RotatingFileHandler` for file logging to `logs/bot.log`.

**Tech Stack:** Python `logging` module.

---

### Task 1: Setup Logger Utility

**Files:**
- Create: `C:\Users\Duoc\Downloads\cs2_trade_bot\app\utils\logger.py`

- [ ] **Step 1: Create the logger utility**

```python
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    # Ensure logs directory exists
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("cs2_bot")
    logger.setLevel(logging.INFO)

    # Console Handler
    c_handler = logging.StreamHandler()
    c_format = logging.Formatter('%(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    logger.addHandler(c_handler)

    # File Handler
    f_handler = RotatingFileHandler(
        os.path.join(log_dir, "bot.log"),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)

    return logger

bot_logger = setup_logger()
```

- [ ] **Step 2: Commit**

```bash
git add app/utils/logger.py
git commit -m "feat: add logging utility"
```

### Task 2: Integrate Logger in main.py

**Files:**
- Modify: `C:\Users\Duoc\Downloads\cs2_trade_bot\app\main.py`

- [ ] **Step 1: Update main.py to use bot_logger**

```python
from app.utils.logger import bot_logger

# Example replacement:
# print("Starting bot...") -> bot_logger.info("Starting bot...")
```

- [ ] **Step 2: Commit**

```bash
git add app/main.py
git commit -m "feat: integrate logger in main.py"
```

### Task 3: Replace Prints in Scrapers

**Files:**
- Modify: `C:\Users\Duoc\Downloads\cs2_trade_bot\app\scrapers\steam.py`
- Modify: `C:\Users\Duoc\Downloads\cs2_trade_bot\app\scrapers\csfloat.py`
- Modify: `C:\Users\Duoc\Downloads\cs2_trade_bot\app\scrapers\daily_dump.py`

- [ ] **Step 1: Update steam.py**
- [ ] **Step 2: Update csfloat.py**
- [ ] **Step 3: Update daily_dump.py**
- [ ] **Step 4: Commit**

```bash
git add app/scrapers/*.py
git commit -m "feat: use bot_logger in scrapers"
```

### Task 4: Replace Prints in Core Modules

**Files:**
- Modify: `C:\Users\Duoc\Downloads\cs2_trade_bot\app\core\arbitrage.py`
- Modify: `C:\Users\Duoc\Downloads\cs2_trade_bot\app\core\contracts.py`
- Modify: `C:\Users\Duoc\Downloads\cs2_trade_bot\app\core\intelligence_loop.py`

- [ ] **Step 1: Update arbitrage.py**
- [ ] **Step 2: Update contracts.py**
- [ ] **Step 3: Update intelligence_loop.py**
- [ ] **Step 4: Commit**

```bash
git add app/core/*.py
git commit -m "feat: use bot_logger in core modules"
```

### Task 5: Final Cleanup and Verification

- [ ] **Step 1: Verify logs directory and bot.log creation**
- [ ] **Step 2: Final commit**

```bash
git commit -m "feat: implement professional rotating logging"
```
