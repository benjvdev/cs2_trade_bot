import requests
from app.database.db_manager import DBManager
from app.utils.logger import bot_logger

BUFF_URL = "https://prices.csgotrader.app/latest/buff163.json"
V6_URL = "https://prices.csgotrader.app/latest/prices_v6.json"

def fetch_daily_dumps():
    db = DBManager()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 1. Buff Dump
    try:
        bot_logger.info(f"Fetching Buff dump from {BUFF_URL}...")
        r = requests.get(BUFF_URL, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        batch = []
        for name, info in data.items():
            price = info.get("starting_at", {}).get("price")
            if price:
                batch.append((name, price, "dump_buff"))
        db.update_prices_batch(batch)
        bot_logger.info(f"✅ Loaded {len(batch)} items from Buff dump.")
    except Exception as e:
        bot_logger.error(f"❌ Error loading Buff dump: {e}")

    # 2. V6 Dump (Steam, Skinport, Skinbaron)
    try:
        bot_logger.info(f"Fetching V6 dump from {V6_URL}...")
        r = requests.get(V6_URL, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        batches = {"dump_steam": [], "dump_skinport": [], "dump_skinbaron": []}
        
        for name, markets in data.items():
            # Steam
            steam_p = markets.get("steam", {}).get("last_24h")
            if steam_p: batches["dump_steam"].append((name, steam_p, "dump_steam"))
            
            # Skinport
            sp_p = markets.get("skinport", {}).get("suggested_price")
            if sp_p: batches["dump_skinport"].append((name, sp_p, "dump_skinport"))
            
            # Skinbaron
            sb_p = markets.get("skinbaron", {}).get("suggested_price")
            if sb_p: batches["dump_skinbaron"].append((name, sb_p, "dump_skinbaron"))
            
        for source, batch in batches.items():
            if batch:
                db.update_prices_batch(batch)
                bot_logger.info(f"✅ Loaded {len(batch)} items from {source}.")
            
    except Exception as e:
        bot_logger.error(f"❌ Error loading V6 dump: {e}")

if __name__ == "__main__":
    fetch_daily_dumps()
