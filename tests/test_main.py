import subprocess
import sys
from types import SimpleNamespace

import pytest

from app import main


def _config():
    return SimpleNamespace(
        steam_limit=7,
        csfloat_limit=11,
        buff_session="buff-session",
    )


def test_run_scrapers_returns_status_dict(monkeypatch):
    buff_calls = []

    monkeypatch.setattr(
        main.daily_dump,
        "fetch_daily_dumps",
        lambda: {"dump_buff": False, "dump_v6": True},
    )
    monkeypatch.setattr(main.steam, "fetch_steam_prices", lambda limit: limit == 7)
    monkeypatch.setattr(
        main.csfloat,
        "fetch_csfloat_prices",
        lambda limit, settings=None: False,
    )

    def fake_run(args, env=None, check=None):
        buff_calls.append((args, env, check))

    monkeypatch.setattr(main.subprocess, "run", fake_run)

    status = main.run_scrapers(_config())

    assert status == {
        "daily_dump": True,
        "steam": True,
        "csfloat": False,
        "buff": True,
    }
    assert buff_calls[0][1]["BUFF_SESSION"] == "buff-session"
    assert buff_calls[0][2] is True


def test_run_scrapers_marks_all_scraper_failures_false(monkeypatch):
    monkeypatch.setattr(
        main.daily_dump,
        "fetch_daily_dumps",
        lambda: {"dump_buff": False, "dump_v6": False},
    )
    monkeypatch.setattr(main.steam, "fetch_steam_prices", lambda limit: False)
    monkeypatch.setattr(
        main.csfloat,
        "fetch_csfloat_prices",
        lambda limit, settings=None: False,
    )

    def fail_run(*args, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd=args[0])

    monkeypatch.setattr(main.subprocess, "run", fail_run)

    status = main.run_scrapers(_config())

    assert status == {
        "daily_dump": False,
        "steam": False,
        "csfloat": False,
        "buff": False,
    }


def test_run_scrapers_continues_after_steam_exception(monkeypatch):
    buff_calls = []
    errors = []

    monkeypatch.setattr(main.daily_dump, "fetch_daily_dumps", lambda: {"dump_buff": True})

    def fail_steam(limit):
        raise RuntimeError("steam setup failed")

    monkeypatch.setattr(main.steam, "fetch_steam_prices", fail_steam)
    monkeypatch.setattr(
        main.csfloat,
        "fetch_csfloat_prices",
        lambda limit, settings=None: True,
    )

    def fake_run(args, env=None, check=None):
        buff_calls.append((args, env, check))

    monkeypatch.setattr(main.subprocess, "run", fake_run)
    monkeypatch.setattr(main.bot_logger, "error", lambda message: errors.append(message))

    status = main.run_scrapers(_config())

    assert status == {
        "daily_dump": True,
        "steam": False,
        "csfloat": True,
        "buff": True,
    }
    assert buff_calls
    assert any("Steam" in message for message in errors)


def test_run_scrapers_continues_after_csfloat_exception(monkeypatch):
    buff_calls = []
    errors = []

    monkeypatch.setattr(main.daily_dump, "fetch_daily_dumps", lambda: {"dump_buff": True})
    monkeypatch.setattr(main.steam, "fetch_steam_prices", lambda limit: True)

    def fail_csfloat(limit, settings=None):
        raise RuntimeError("csfloat setup failed")

    monkeypatch.setattr(main.csfloat, "fetch_csfloat_prices", fail_csfloat)

    def fake_run(args, env=None, check=None):
        buff_calls.append((args, env, check))

    monkeypatch.setattr(main.subprocess, "run", fake_run)
    monkeypatch.setattr(main.bot_logger, "error", lambda message: errors.append(message))

    status = main.run_scrapers(_config())

    assert status == {
        "daily_dump": True,
        "steam": True,
        "csfloat": False,
        "buff": True,
    }
    assert buff_calls
    assert any("CSFloat" in message for message in errors)


def test_main_default_path_refuses_analysis_when_all_scrapers_fail(monkeypatch):
    config = _config()
    analysis_called = False

    def fail_if_called(*args, **kwargs):
        nonlocal analysis_called
        analysis_called = True
        raise AssertionError("analysis should not run when all scrapers fail")

    monkeypatch.setattr(sys, "argv", ["bot"])
    monkeypatch.setattr(main, "load_settings", lambda _path: config)
    monkeypatch.setattr(
        main,
        "run_scrapers",
        lambda _config: {
            "daily_dump": False,
            "steam": False,
            "csfloat": False,
            "buff": False,
        },
    )
    monkeypatch.setattr(main, "run_analysis", fail_if_called)
    monkeypatch.setattr(main, "generate_reports", fail_if_called)

    with pytest.raises(
        RuntimeError,
        match="All scrapers failed; refusing to analyze stale data.",
    ):
        main.main()

    assert analysis_called is False
