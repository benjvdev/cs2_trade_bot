import json

import pytest

from app.core.config import load_settings


def write_config(tmp_path, data, *, ensure_ascii=True):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(data, ensure_ascii=ensure_ascii), encoding="utf-8")
    return config_path


def test_load_settings_preserves_missing_file_error(tmp_path):
    missing_path = tmp_path / "missing-config.json"

    with pytest.raises(FileNotFoundError) as exc_info:
        load_settings(str(missing_path))

    assert str(missing_path) in str(exc_info.value)


def test_load_settings_reads_raw_utf8_json(tmp_path, monkeypatch):
    monkeypatch.delenv("BUFF_SESSION", raising=False)
    raw_buff_session = "session-\u00f1-\u6771\u4eac"

    config_path = write_config(
        tmp_path,
        {"buff_session": raw_buff_session},
        ensure_ascii=False,
    )

    assert raw_buff_session in config_path.read_text(encoding="utf-8")

    settings = load_settings(str(config_path))

    assert settings.buff_session == raw_buff_session


def test_load_settings_exposes_skinport_and_skinbaron_api_keys(tmp_path, monkeypatch):
    monkeypatch.delenv("SKINPORT_API_KEY", raising=False)
    monkeypatch.delenv("SKINBARON_API_KEY", raising=False)

    config_path = write_config(
        tmp_path,
        {
            "min_roi": 20.0,
            "max_budget": 75.0,
            "buff_session": "from-config",
            "skinport_api_key": "skinport-from-config",
            "skinbaron_api_key": "skinbaron-from-config",
        },
    )

    settings = load_settings(str(config_path))

    assert settings.skinport_api_key == "skinport-from-config"
    assert settings.skinbaron_api_key == "skinbaron-from-config"


def test_environment_secrets_override_config_file_values(tmp_path, monkeypatch):
    monkeypatch.setenv("BUFF_SESSION", "buff-from-env")
    monkeypatch.setenv("CSFLOAT_API_KEY", "csfloat-from-env")
    monkeypatch.setenv("SKINPORT_API_KEY", "skinport-from-env")
    monkeypatch.setenv("SKINBARON_API_KEY", "skinbaron-from-env")

    config_path = write_config(
        tmp_path,
        {
            "min_roi": 20.0,
            "max_budget": 75.0,
            "buff_session": "buff-from-config",
            "csfloat_api_key": "csfloat-from-config",
            "skinport_api_key": "skinport-from-config",
            "skinbaron_api_key": "skinbaron-from-config",
        },
    )

    settings = load_settings(str(config_path))

    assert settings.buff_session == "buff-from-env"
    assert settings.csfloat_api_key == "csfloat-from-env"
    assert settings.skinport_api_key == "skinport-from-env"
    assert settings.skinbaron_api_key == "skinbaron-from-env"


def test_load_settings_uses_dependency_baseline_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("BUFF_SESSION", raising=False)
    monkeypatch.delenv("CSFLOAT_API_KEY", raising=False)
    monkeypatch.delenv("SKINPORT_API_KEY", raising=False)
    monkeypatch.delenv("SKINBARON_API_KEY", raising=False)

    config_path = write_config(tmp_path, {})

    settings = load_settings(str(config_path))

    assert settings.min_roi == 15.0
    assert settings.max_budget == 50.0
    assert settings.buff_session == ""
    assert settings.steam_limit == 50
    assert settings.csfloat_limit == 50
    assert settings.rmb_to_usd == 0.14
    assert settings.batch_size == 100
    assert settings.batch_sleep == 5.0
    assert settings.max_price_age_hours == 24.0
    assert settings.csfloat_api_key is None
    assert settings.skinport_api_key is None
    assert settings.skinbaron_api_key is None
