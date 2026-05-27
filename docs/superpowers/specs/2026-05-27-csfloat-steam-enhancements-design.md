# CSFloat API Key & Anti-Ban Enhancements Design

**Goal:** Fix CSFloat 403 errors using an API Key and add anti-ban jitter (random delays) to Steam and Buff scrapers to improve reliability and avoid being blocked.

## Architecture

1.  **Configuration:** Update `config.json` to store the `csfloat_api_key`.
2.  **CSFloat Scraper:** Modify `app/scrapers/csfloat.py` to load the API key and include it in the `Authorization` header if present.
3.  **Steam Scraper:** Modify `app/scrapers/steam.py` to add random delays (`random.uniform(1.0, 3.0)`) between retries or before requests to mimic human behavior.
4.  **Buff Scraper:** Modify `app/scrapers/buff/index.js` to add a random delay (`Math.random() * 2000 + 1000`) before navigating to the API URL.

## Components

### 1. Configuration (`config.json`)
- Add `csfloat_api_key` field.

### 2. CSFloat Scraper (`app/scrapers/csfloat.py`)
- Load `config.json` to get the API key.
- Update `fetch_csfloat_prices` to accept an optional `api_key`.
- Use `scraper.get(url, headers={"Authorization": api_key}, ...)` if `api_key` is provided.

### 3. Steam Scraper (`app/scrapers/steam.py`)
- Import `random`.
- Add jitter using `time.sleep()`.

### 4. Buff Scraper (`app/scrapers/buff/index.js`)
- Add delay using `page.waitForTimeout()`.

## Data Flow
1. `app/main.py` loads the configuration.
2. Configuration is passed to scrapers or scrapers load it themselves.
3. Scrapers execute with enhanced logic (headers, delays).

## Error Handling
- Handle cases where `config.json` might be missing or the key is not set (graceful fallback for CSFloat).
- Ensure Steam's existing retry logic remains functional with added jitter.

## Testing
- Verify CSFloat sends the header when the key is configured.
- Verify Steam and Buff have observable delays during execution.
