import sqlite3
import os
from app.utils.logger import bot_logger

class DBManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Default to project root / cs2_skins.db
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.db_path = os.path.join(base_dir, "cs2_skins.db")
        else:
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
                bot_logger.warning("Old prices table detected. Migrating to multi-source schema...")
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
        
    def update_prices_batch(self, price_data_list):
        """
        Updates multiple prices in a single transaction.
        price_data_list: List of tuples (name, price, source)
        """
        if not price_data_list:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        try:
            cursor.executemany('''
                INSERT OR REPLACE INTO prices (market_hash_name, price, source, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', price_data_list)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
        
    def get_price(self, name, source):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT price FROM prices WHERE market_hash_name = ? AND source = ?', (name, source))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None
