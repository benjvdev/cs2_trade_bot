import requests
from app.database.db_manager import DBManager
from app.utils.logger import bot_logger

BUFF_URL = "https://prices.csgotrader.app/latest/buff163.json"
STEAM_URL = "https://prices.csgotrader.app/latest/steam.json"
SKINPORT_URL = "https://prices.csgotrader.app/latest/skinport.json"


def fetch_json(url, headers):
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP status {response.status_code} for {url}")

    content_type = response.headers.get("content-type") or response.headers.get("Content-Type") or ""
    if "json" not in content_type.lower():
        raise RuntimeError(f"Unexpected content type {content_type} for {url}")

    return response.json()


def fetch_daily_dumps():
    db = DBManager()
    status = {
        "dump_buff": False,
        "dump_steam": False,
        "dump_skinport": False,
        "dump_skinbaron": False,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 1. Buff Dump
    try:
        bot_logger.info(f"Fetching Buff dump from {BUFF_URL}...")
        data = fetch_json(BUFF_URL, headers)
        batch = []
        for name, info in data.items():
            price = info.get("starting_at", {}).get("price")
            if price:
                batch.append((name, price, "dump_buff"))
        if batch:
            db.update_prices_batch(batch)
            status["dump_buff"] = True
            bot_logger.info(f"Loaded {len(batch)} items from Buff dump.")
        else:
            bot_logger.warning("No parseable items found in Buff dump.")
    except Exception as e:
        bot_logger.error(f"Error loading Buff dump: {e}")

    # 2. Steam Dump
    try:
        bot_logger.info(f"Fetching Steam dump from {STEAM_URL}...")
        data = fetch_json(STEAM_URL, headers)
        batch = []
        for name, info in data.items():
            price = info.get("last_24h")
            if price:
                batch.append((name, price, "dump_steam"))
        if batch:
            db.update_prices_batch(batch)
            status["dump_steam"] = True
            bot_logger.info(f"Loaded {len(batch)} items from dump_steam.")
        else:
            bot_logger.warning("No parseable items found in Steam dump.")

    except Exception as e:
        bot_logger.error(f"Error loading Steam dump: {e}")

    # 3. Skinport Dump
    try:
        bot_logger.info(f"Fetching Skinport dump from {SKINPORT_URL}...")
        data = fetch_json(SKINPORT_URL, headers)
        batch = []
        for name, info in data.items():
            price = info.get("suggested_price") or info.get("starting_at")
            if price:
                batch.append((name, price, "dump_skinport"))
        if batch:
            db.update_prices_batch(batch)
            status["dump_skinport"] = True
            bot_logger.info(f"Loaded {len(batch)} items from dump_skinport.")
        else:
            bot_logger.warning("No parseable items found in Skinport dump.")

    except Exception as e:
        bot_logger.error(f"Error loading Skinport dump: {e}")

    bot_logger.warning("Skinbaron dump endpoint is not currently available; skipping dump_skinbaron.")

    return status


if __name__ == "__main__":
    fetch_daily_dumps()
