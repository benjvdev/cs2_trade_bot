# Database Manager (Multi-source) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a centralized `DBManager` to handle multi-source price data and static skin data.

**Architecture:** A single `DBManager` class using `sqlite3` with a composite primary key on the `prices` table. Includes migration logic for existing databases.

**Tech Stack:** Python, `sqlite3`.

---

### Task 1: Create DBManager

**Files:**
- Create: `app/database/db_manager.py`

- [ ] **Step 1: Write the DBManager class**

```python
import sqlite3
import os

class DBManager:
    def __init__(self, db_path="data/cs2_skins.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for skins (static data)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skins (
                id TEXT PRIMARY KEY, 
                name TEXT, 
                rarity TEXT, 
                collection TEXT,
                min_float REAL, 
                max_float REAL, 
                image_url TEXT
            )
        ''')
        
        # Handle migration for prices table if it exists but is old style
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'")
        if cursor.fetchone():
            # Check if it has the composite primary key (market_hash_name, source)
            cursor.execute("PRAGMA table_info(prices)")
            columns = cursor.fetchall()
            pk_count = sum(1 for col in columns if col[5] > 0)
            
            if pk_count < 2:
                print("⚠️ Old prices table detected. Migrating to multi-source schema...")
                cursor.execute("ALTER TABLE prices RENAME TO prices_old")
                cursor.execute('''
                    CREATE TABLE prices (
                        market_hash_name TEXT, 
                        price REAL, 
                        source TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (market_hash_name, source)
                    )
                ''')
                cursor.execute('''
                    INSERT OR IGNORE INTO prices (market_hash_name, price, source, updated_at)
                    SELECT market_hash_name, price, source, updated_at FROM prices_old
                ''')
                cursor.execute("DROP TABLE prices_old")
        else:
            # Table for prices (dynamic data, multi-source)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prices (
                    market_hash_name TEXT, 
                    price REAL, 
                    source TEXT,
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
        
    def get_price(self, name, source):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT price FROM prices WHERE market_hash_name = ? AND source = ?', (name, source))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None
```

### Task 2: Verify and Test

**Files:**
- Create: `test_db.py`

- [ ] **Step 1: Write the test script**

```python
from app.database.db_manager import DBManager
import os

def test_db():
    db_path = "data/test_skins.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    db = DBManager(db_path)
    
    # Test Update
    db.update_price("AK-47 | Redline (Field-Tested)", 20.5, "buff")
    db.update_price("AK-47 | Redline (Field-Tested)", 22.0, "steam")
    
    # Test Retrieval
    price_buff = db.get_price("AK-47 | Redline (Field-Tested)", "buff")
    price_steam = db.get_price("AK-47 | Redline (Field-Tested)", "steam")
    
    print(f"Buff Price: {price_buff}")
    print(f"Steam Price: {price_steam}")
    
    assert price_buff == 20.5
    assert price_steam == 22.0
    print("✅ DB Manager tests passed!")
    
    os.remove(db_path)

if __name__ == "__main__":
    test_db()
```

- [ ] **Step 2: Run the test**

Run: `python test_db.py`
Expected: `✅ DB Manager tests passed!`

- [ ] **Step 3: Cleanup**

Remove `test_db.py`.
