from app.scrapers import steam


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class FakeScraper:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeDB:
    def __init__(self):
        self.rows = []
        self.update_calls = 0

    def update_prices_batch(self, rows):
        self.update_calls += 1
        self.rows.extend(rows)


class FakeLogger:
    def __init__(self):
        self.warnings = []
        self.errors = []

    def info(self, message):
        pass

    def warning(self, message):
        self.warnings.append(message)

    def error(self, message):
        self.errors.append(message)


def _install_no_side_effect_dependencies(monkeypatch, scraper, db):
    monkeypatch.setattr(steam.cloudscraper, "create_scraper", lambda: scraper)
    monkeypatch.setattr(steam, "DBManager", lambda: db)
    monkeypatch.setattr(steam.random, "uniform", lambda *_args: 0)

    sleeps = []
    monkeypatch.setattr(steam.time, "sleep", lambda seconds: sleeps.append(seconds))

    logger = FakeLogger()
    monkeypatch.setattr(steam, "bot_logger", logger)

    return sleeps, logger


def test_fetch_steam_prices_retries_transient_exception_then_updates_db(monkeypatch):
    db = FakeDB()
    scraper = FakeScraper(
        [
            RuntimeError("temporary Steam failure"),
            FakeResponse(
                payload={
                    "success": True,
                    "results": [
                        {
                            "hash_name": "AK-47 | Redline (Field-Tested)",
                            "sell_price": 1234,
                        }
                    ],
                }
            ),
        ]
    )
    sleeps, logger = _install_no_side_effect_dependencies(monkeypatch, scraper, db)

    result = steam.fetch_steam_prices(limit=1)

    assert result is True
    assert len(scraper.calls) == 2
    assert db.update_calls == 1
    assert db.rows == [("AK-47 | Redline (Field-Tested)", 12.34, "steam")]
    assert 20 in sleeps
    assert len(logger.warnings) == 1
    assert logger.errors == []


def test_fetch_steam_prices_returns_false_after_exception_retries_exhausted(monkeypatch):
    db = FakeDB()
    scraper = FakeScraper(
        [
            RuntimeError("Steam down 1"),
            RuntimeError("Steam down 2"),
            RuntimeError("Steam down 3"),
            RuntimeError("Steam down 4"),
        ]
    )
    sleeps, logger = _install_no_side_effect_dependencies(monkeypatch, scraper, db)

    result = steam.fetch_steam_prices(limit=1)

    assert result is False
    assert len(scraper.calls) == 4
    assert db.update_calls == 0
    assert 20 in sleeps
    assert 40 in sleeps
    assert 80 in sleeps
    assert len(logger.warnings) == 3
    assert len(logger.errors) == 1


def test_fetch_steam_prices_stops_429_retries_without_extra_attempt(monkeypatch):
    db = FakeDB()
    scraper = FakeScraper(
        [
            FakeResponse(status_code=429),
            FakeResponse(status_code=429),
            FakeResponse(status_code=429),
            FakeResponse(status_code=429),
        ]
    )
    sleeps, logger = _install_no_side_effect_dependencies(monkeypatch, scraper, db)

    result = steam.fetch_steam_prices(limit=1)

    assert result is False
    assert len(scraper.calls) == 4
    assert db.update_calls == 0
    assert sleeps.count(30) == 1
    assert sleeps.count(60) == 1
    assert sleeps.count(120) == 1
    assert not any(240 == sleep for sleep in sleeps)
    assert len(logger.warnings) == 3
    assert len(logger.errors) == 1
