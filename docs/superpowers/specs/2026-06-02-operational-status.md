# Operational Status - 2026-06-02

This status records what the stabilization worktree can claim today. It is limited to the current implementation and unit-test scope; live marketplace reliability still needs validation.

## Working

- Unit tests for core math/probability and arbitrage basics pass in the stabilization scope.
- The price DB schema supports multi-source prices by storing rows keyed by `(market_hash_name, source)`.
- Price records include `updated_at`, which gives the bot enough schema support for source freshness checks.
- Daily dump ingestion can store Buff, Steam and Skinport dump prices when CSGOTrader endpoints return valid JSON. Skinbaron is currently marked unavailable because no active JSON endpoint was found.

## Fixed In Stabilization Plan

- The CSFloat parser accepts both legacy list payloads and current wrapped payloads with `data` and `cursor`.
- CSFloat pagination is bounded, supports cursor advancement, and can target specific `market_hash_name` values for verification batches.
- Scrapers now expose observable status: Steam and CSFloat return booleans, daily dump returns per-dump status, and `main.run_scrapers` aggregates daily dump, Steam, CSFloat and Buff status.
- The default/full run refuses to analyze when every scraper/dump reports failure, avoiding a report generated entirely from known-failed refresh attempts.
- The arbitrage engine filters sources that are not in its trusted-source list and prioritizes live data over dump data for the same market.
- Source-age stale marking is not claimed as complete here. The config has `max_price_age_hours` and DB rows have `updated_at`, but automatic per-source freshness-window report marking is still being stabilized.

## Still Requires Live Validation

- Buff session validity with real cookies, current login behavior and Cloudflare responses.
- CSGOTrader daily dump availability, JSON content type, and field stability for Buff, Steam and Skinport endpoints.
- A valid Skinbaron JSON dump endpoint or authenticated integration.
- Steam rate limits and retry behavior under real 429 or temporary block conditions.
- End-to-end freshness-window behavior once per-source age marking is fully wired into analysis/reporting.
