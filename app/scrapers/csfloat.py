import os
from urllib.parse import urlencode

import cloudscraper

from app.core.config import Settings, load_settings
from app.database.db_manager import DBManager
from app.utils.logger import bot_logger


CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
BASE_URL = "https://csfloat.com/api/v1/listings"
MAX_PAGE_LIMIT = 50


def extract_listings(payload):
    if isinstance(payload, list):
        return payload, None

    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return payload["data"], payload.get("cursor")

    raise ValueError("Unexpected CSFloat response format")


def build_headers(settings):
    headers = {
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    api_key = getattr(settings, "csfloat_api_key", None) if settings else None
    if api_key:
        headers["Authorization"] = api_key

    return headers


def fetch_csfloat_prices(
    limit=50,
    settings: Settings = None,
    db_manager=None,
    scraper=None,
    market_hash_names=None,
):
    """
    Fetches CS2 item prices from CSFloat API.
    """
    if settings is None:
        try:
            settings = load_settings(CONFIG_PATH)
        except Exception as e:
            bot_logger.warning(f"Could not load CSFloat settings: {e}. Continuing without API key.")
            settings = None

    try:
        http = scraper if scraper is not None else cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "desktop": True,
            }
        )
        db = db_manager if db_manager is not None else DBManager()
        headers = build_headers(settings)
        prices_by_item = {}

        bot_logger.info(f"Fetching {limit} items from CSFloat...")

        def collect_prices(listings):
            for listing in listings:
                if not isinstance(listing, dict):
                    continue
                if listing.get("state") != "listed" or listing.get("type") != "buy_now":
                    continue

                item = listing.get("item") or {}
                if not isinstance(item, dict):
                    continue

                hash_name = item.get("market_hash_name")
                price_cents = listing.get("price")

                if not hash_name or price_cents is None:
                    continue

                try:
                    price = float(price_cents) / 100.0
                except (TypeError, ValueError):
                    continue

                current_price = prices_by_item.get(hash_name)
                if current_price is None or price < current_price:
                    prices_by_item[hash_name] = price

        if market_hash_names is not None:
            request_limit = min(MAX_PAGE_LIMIT, max(limit, 1))
            for market_hash_name in market_hash_names:
                params = {
                    "limit": request_limit,
                    "sort_by": "lowest_price",
                    "type": "buy_now",
                    "market_hash_name": market_hash_name,
                }

                response = http.get(f"{BASE_URL}?{urlencode(params)}", headers=headers, timeout=30)

                if response.status_code != 200:
                    bot_logger.error(f"CSFloat API Error: {response.status_code}")
                    return False

                listings, _ = extract_listings(response.json())
                collect_prices(listings)
        else:
            cursor = None
            seen_cursors = set()
            pages_fetched = 0
            max_pages = max(1, ((max(limit, 0) + MAX_PAGE_LIMIT - 1) // MAX_PAGE_LIMIT) + 5)

            while len(prices_by_item) < limit and pages_fetched < max_pages:
                remaining_needed = limit - len(prices_by_item)
                params = {
                    "limit": min(MAX_PAGE_LIMIT, remaining_needed),
                    "sort_by": "lowest_price",
                    "type": "buy_now",
                }
                if cursor:
                    params["cursor"] = cursor

                response = http.get(f"{BASE_URL}?{urlencode(params)}", headers=headers, timeout=30)
                pages_fetched += 1

                if response.status_code != 200:
                    bot_logger.error(f"CSFloat API Error: {response.status_code}")
                    return False

                listings, next_cursor = extract_listings(response.json())
                collect_prices(listings)

                if not next_cursor or not listings:
                    break

                if next_cursor == cursor or next_cursor in seen_cursors:
                    bot_logger.warning("Stopping CSFloat pagination because cursor did not advance.")
                    break

                seen_cursors.add(next_cursor)
                cursor = next_cursor

            if pages_fetched >= max_pages and len(prices_by_item) < limit:
                bot_logger.warning("Stopping CSFloat pagination after reaching the page limit.")

        if not prices_by_item:
            bot_logger.warning("No valid items found in CSFloat response.")
            return False

        rows = [(hash_name, price, "csfloat") for hash_name, price in prices_by_item.items()]
        db.update_prices_batch(rows)
        bot_logger.info(f"Successfully updated {len(rows)} items from CSFloat.")
        return True

    except Exception as e:
        bot_logger.error(f"Error fetching CSFloat prices: {e}")
        return False


if __name__ == "__main__":
    fetch_csfloat_prices(10)
