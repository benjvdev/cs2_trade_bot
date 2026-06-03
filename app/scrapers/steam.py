import time
import random
import cloudscraper
from app.database.db_manager import DBManager
from app.utils.logger import bot_logger

def fetch_steam_prices(limit=100):
    """
    Fetches CS2 item prices from Steam Community Market.
    """
    url = f"https://steamcommunity.com/market/search/render/?query=&start=0&count={limit}&search_descriptions=0&sort_column=popular&sort_dir=desc&appid=730&norender=1"
    
    scraper = cloudscraper.create_scraper()
    db = DBManager()
    
    bot_logger.info(f"🚀 Fetching {limit} items from Steam...")
    
    # Add initial jitter
    time.sleep(random.uniform(1.0, 3.0))
    
    max_retries = 3
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            # Add jitter before each attempt if it's a retry
            if retry_count > 0:
                time.sleep(random.uniform(2.0, 5.0))
            
            # Steam is very strict, so we might need to handle 429 Too Many Requests
            response = scraper.get(url, timeout=30)
            
            if response.status_code == 429:
                if retry_count >= max_retries:
                    bot_logger.error("❌ Max retries reached for Steam.")
                    return False

                wait_time = 2**retry_count * 30
                bot_logger.warning(f"⚠️ Steam Rate Limit hit (429). Retrying in {wait_time} seconds... ({retry_count + 1}/{max_retries})")
                time.sleep(wait_time)
                retry_count += 1
                continue
                
            if response.status_code != 200:
                bot_logger.error(f"❌ Steam API Error: {response.status_code}")
                return False
                
            data = response.json()
            if not data.get("success"):
                bot_logger.error("❌ Steam API success=False")
                return False
                
            results = data.get("results", [])
            batch_data = []
            
            for item in results:
                hash_name = item.get("hash_name")
                # sell_price is in cents (integer)
                sell_price_cents = item.get("sell_price")
                
                if hash_name and sell_price_cents:
                    # Convert to float (e.g., 123 -> 1.23)
                    price_float = float(sell_price_cents) / 100.0
                    batch_data.append((hash_name, price_float, "steam"))
            
            if batch_data:
                db.update_prices_batch(batch_data)
                bot_logger.info(f"✅ Successfully updated {len(batch_data)} items from Steam.")
                return True
            else:
                bot_logger.warning("⚠️ No valid items found in Steam response.")
                return False
                
        except Exception as e:
            retry_count += 1
            if retry_count > max_retries:
                bot_logger.error(f"Error fetching Steam prices after retries: {e}")
                return False

            wait_time = 2**retry_count * 10
            bot_logger.warning(f"Steam request failed. Retrying in {wait_time}s: {e}")
            time.sleep(wait_time)
            
    bot_logger.error("❌ Max retries reached for Steam.")
    return False

if __name__ == "__main__":
    fetch_steam_prices(10)
