import os
import json
import cloudscraper
from app.database.db_manager import DBManager
from app.core.config import load_settings, Settings

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")

def fetch_csfloat_prices(limit=100, settings: Settings = None):
    """
    Fetches CS2 item prices from CSFloat API.
    """
    if settings is None:
        try:
            settings = load_settings(CONFIG_PATH)
        except Exception:
            settings = None

    # CSFloat API listings endpoint
    url = f"https://csfloat.com/api/v1/listings?limit={limit}"
    
    api_key = settings.csfloat_api_key if settings else None
    headers = {}
    if api_key:
        headers["Authorization"] = api_key

    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    db = DBManager()
    
    print(f"🚀 Fetching {limit} items from CSFloat...")
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    if api_key:
        headers["Authorization"] = api_key
    
    try:
        response = scraper.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ CSFloat API Error: {response.status_code}")
            return False
            
        data = response.json()
        
        # CSFloat returns a list of listings
        if not isinstance(data, list):
            print("❌ CSFloat API unexpected response format (not a list)")
            return False
            
        batch_data = []
        for listing in data:
            item = listing.get("item", {})
            hash_name = item.get("market_hash_name")
            price_cents = listing.get("price")
            
            if hash_name and price_cents is not None:
                # CSFloat prices are in cents, divide by 100
                price_float = float(price_cents) / 100.0
                batch_data.append((hash_name, price_float, "csfloat"))
                
        if batch_data:
            db.update_prices_batch(batch_data)
            print(f"✅ Successfully updated {len(batch_data)} items from CSFloat.")
            return True
        else:
            print("⚠️ No valid items found in CSFloat response.")
            return False
            
    except Exception as e:
        print(f"❌ Error fetching CSFloat prices: {e}")
        return False

if __name__ == "__main__":
    fetch_csfloat_prices(10)
