from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest

from app.scrapers import csfloat


class FakeResponse:
    def __init__(self, status_code=200, payload=None, json_error=None):
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise self._json_error
        return self._payload


class FakeScraper:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self._responses.pop(0)


class FakeDB:
    def __init__(self):
        self.rows = []

    def update_prices_batch(self, rows):
        self.rows.extend(rows)


class GuardedRepeatingScraper:
    def __init__(self, response, max_calls=3):
        self.response = response
        self.max_calls = max_calls
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if len(self.calls) > self.max_calls:
            raise RuntimeError("pagination was not bounded")
        return self.response


def listed_item(name, price=1000):
    return {
        "state": "listed",
        "type": "buy_now",
        "price": price,
        "item": {"market_hash_name": name},
    }


def test_extract_listings_accepts_current_wrapped_payload():
    payload = {"data": [{"id": "listing-1"}], "cursor": "next-page"}

    listings, cursor = csfloat.extract_listings(payload)

    assert listings == payload["data"]
    assert cursor == "next-page"


def test_extract_listings_accepts_legacy_list_payload():
    payload = [{"id": "legacy-listing"}]

    listings, cursor = csfloat.extract_listings(payload)

    assert listings == payload
    assert cursor is None


def test_extract_listings_rejects_unexpected_payload_format():
    with pytest.raises(ValueError):
        csfloat.extract_listings({"results": []})


def test_build_headers_adds_json_browser_and_optional_authorization():
    headers = csfloat.build_headers(SimpleNamespace(csfloat_api_key="secret-key"))

    assert headers["Accept"] == "application/json"
    assert "Mozilla/5.0" in headers["User-Agent"]
    assert headers["Authorization"] == "secret-key"

    anonymous_headers = csfloat.build_headers(SimpleNamespace(csfloat_api_key=None))

    assert "Authorization" not in anonymous_headers


def test_fetch_csfloat_prices_updates_db_from_wrapped_payload_with_injected_dependencies():
    db = FakeDB()
    scraper = FakeScraper(
        [
            FakeResponse(
                payload={
                    "data": [
                        {
                            "state": "listed",
                            "type": "buy_now",
                            "price": 1234,
                            "item": {"market_hash_name": "AK-47 | Redline (Field-Tested)"},
                        },
                        {
                            "state": "sold",
                            "type": "buy_now",
                            "price": 9999,
                            "item": {"market_hash_name": "Ignored Sold Item"},
                        },
                    ],
                    "cursor": "next-page",
                }
            ),
            FakeResponse(
                payload={
                    "data": [
                        {
                            "state": "listed",
                            "type": "buy_now",
                            "price": 250,
                            "item": {"market_hash_name": "M4A1-S | Cyrex (Minimal Wear)"},
                        }
                    ],
                    "cursor": None,
                }
            ),
        ]
    )
    settings = SimpleNamespace(csfloat_api_key="secret-key")

    result = csfloat.fetch_csfloat_prices(
        limit=2,
        settings=settings,
        db_manager=db,
        scraper=scraper,
    )

    assert result is True
    assert db.rows == [
        ("AK-47 | Redline (Field-Tested)", 12.34, "csfloat"),
        ("M4A1-S | Cyrex (Minimal Wear)", 2.5, "csfloat"),
    ]

    first_url, first_kwargs = scraper.calls[0]
    first_query = parse_qs(urlparse(first_url).query)
    assert first_url.startswith(csfloat.BASE_URL)
    assert first_query["sort_by"] == ["lowest_price"]
    assert first_query["type"] == ["buy_now"]
    assert first_kwargs["headers"]["Authorization"] == "secret-key"

    second_url, _ = scraper.calls[1]
    second_query = parse_qs(urlparse(second_url).query)
    assert second_query["cursor"] == ["next-page"]


def test_fetch_csfloat_prices_caps_page_limit_at_50():
    db = FakeDB()
    scraper = FakeScraper(
        [
            FakeResponse(
                payload={
                    "data": [listed_item(f"Item {index}", 1000 + index) for index in range(50)],
                    "cursor": "next-page",
                }
            ),
            FakeResponse(
                payload={
                    "data": [listed_item(f"Item {index}", 1000 + index) for index in range(50, 75)],
                    "cursor": None,
                }
            ),
        ]
    )

    result = csfloat.fetch_csfloat_prices(
        limit=75,
        settings=SimpleNamespace(csfloat_api_key=None),
        db_manager=db,
        scraper=scraper,
    )

    assert result is True
    assert len(db.rows) == 75

    first_query = parse_qs(urlparse(scraper.calls[0][0]).query)
    second_query = parse_qs(urlparse(scraper.calls[1][0]).query)
    assert first_query["limit"] == ["50"]
    assert second_query["limit"] == ["25"]


def test_fetch_csfloat_prices_stops_on_repeated_cursor_without_db_write():
    db = FakeDB()
    scraper = GuardedRepeatingScraper(
        FakeResponse(
            payload={
                "data": [
                    {
                        "state": "sold",
                        "type": "buy_now",
                        "price": 1000,
                        "item": {"market_hash_name": "Ignored Item"},
                    }
                ],
                "cursor": "same-cursor",
            }
        )
    )

    result = csfloat.fetch_csfloat_prices(
        limit=1,
        settings=SimpleNamespace(csfloat_api_key=None),
        db_manager=db,
        scraper=scraper,
    )

    assert result is False
    assert db.rows == []
    assert len(scraper.calls) == 2


@pytest.mark.parametrize("failing_dependency", ["scraper", "db"])
def test_fetch_csfloat_prices_returns_false_when_default_dependencies_fail(monkeypatch, failing_dependency):
    if failing_dependency == "scraper":
        def fail_create_scraper(*args, **kwargs):
            raise RuntimeError("scraper construction failed")

        monkeypatch.setattr(csfloat.cloudscraper, "create_scraper", fail_create_scraper)
    else:
        monkeypatch.setattr(
            csfloat.cloudscraper,
            "create_scraper",
            lambda *args, **kwargs: FakeScraper([]),
        )

        def fail_db_manager():
            raise RuntimeError("db construction failed")

        monkeypatch.setattr(csfloat, "DBManager", fail_db_manager)

    result = csfloat.fetch_csfloat_prices(
        limit=1,
        settings=SimpleNamespace(csfloat_api_key=None),
    )

    assert result is False


def test_fetch_csfloat_prices_keeps_lowest_duplicate_item_price():
    db = FakeDB()
    scraper = FakeScraper(
        [
            FakeResponse(
                payload={
                    "data": [
                        listed_item("AK-47 | Redline (Field-Tested)", 1000),
                        listed_item("AK-47 | Redline (Field-Tested)", 2500),
                    ],
                    "cursor": None,
                }
            )
        ]
    )

    result = csfloat.fetch_csfloat_prices(
        limit=2,
        settings=SimpleNamespace(csfloat_api_key=None),
        db_manager=db,
        scraper=scraper,
    )

    assert result is True
    assert db.rows == [("AK-47 | Redline (Field-Tested)", 10.0, "csfloat")]


def test_fetch_csfloat_prices_requests_only_provided_market_hash_names():
    db = FakeDB()
    scraper = FakeScraper(
        [
            FakeResponse(
                payload={
                    "data": [listed_item("AK-47 | Slate (Field-Tested)", 1000)],
                    "cursor": "ignored-target-cursor",
                }
            ),
            FakeResponse(
                payload={
                    "data": [listed_item("M4A1-S | Printstream (Minimal Wear)", 2500)],
                    "cursor": None,
                }
            ),
        ]
    )
    requested_names = [
        "AK-47 | Slate (Field-Tested)",
        "M4A1-S | Printstream (Minimal Wear)",
    ]

    result = csfloat.fetch_csfloat_prices(
        limit=10,
        settings=SimpleNamespace(csfloat_api_key=None),
        db_manager=db,
        scraper=scraper,
        market_hash_names=requested_names,
    )

    assert result is True
    assert db.rows == [
        ("AK-47 | Slate (Field-Tested)", 10.0, "csfloat"),
        ("M4A1-S | Printstream (Minimal Wear)", 25.0, "csfloat"),
    ]
    assert len(scraper.calls) == 2

    queries = [parse_qs(urlparse(url).query) for url, _ in scraper.calls]
    assert [query["market_hash_name"][0] for query in queries] == requested_names
    assert all(query["type"] == ["buy_now"] for query in queries)


@pytest.mark.parametrize(
    "response",
    [
        FakeResponse(status_code=403, json_error=ValueError("blocked HTML")),
        FakeResponse(status_code=200, json_error=ValueError("not JSON")),
    ],
)
def test_fetch_csfloat_prices_rejects_non_json_or_blocked_response_without_db_write(response):
    db = FakeDB()
    scraper = FakeScraper([response])

    result = csfloat.fetch_csfloat_prices(
        limit=1,
        settings=SimpleNamespace(csfloat_api_key=None),
        db_manager=db,
        scraper=scraper,
    )

    assert result is False
    assert db.rows == []


def test_run_scrapers_logs_failed_steam_and_csfloat_scrapers(monkeypatch):
    from app import main

    warnings = []

    monkeypatch.setattr(main.daily_dump, "fetch_daily_dumps", lambda: None)
    monkeypatch.setattr(main.steam, "fetch_steam_prices", lambda limit: False)
    monkeypatch.setattr(
        main.csfloat,
        "fetch_csfloat_prices",
        lambda limit, settings=None: False,
    )
    monkeypatch.setattr(main.subprocess, "run", lambda *args, **kwargs: None)
    monkeypatch.setattr(main.bot_logger, "warning", lambda message: warnings.append(message))

    main.run_scrapers(
        SimpleNamespace(
            steam_limit=1,
            csfloat_limit=1,
            buff_session="",
        )
    )

    assert any("Steam" in message and "CSFloat" in message for message in warnings)
