import pytest
from unittest.mock import MagicMock, patch
from app.scrapers import daily_dump


def _response(status_code=200, content_type="application/json", json_data=None):
    response = MagicMock()
    response.status_code = status_code
    response.headers = {"content-type": content_type}
    response.json.return_value = json_data if json_data is not None else {}
    return response


def _status(buff=False, steam=False, skinport=False, skinbaron=False):
    return {
        "dump_buff": buff,
        "dump_steam": steam,
        "dump_skinport": skinport,
        "dump_skinbaron": skinbaron,
    }

@patch('app.scrapers.daily_dump.requests.get')
@patch('app.scrapers.daily_dump.DBManager')
def test_fetch_daily_dumps(mock_db_class, mock_get):
    # Mock DBManager
    mock_db = MagicMock()
    mock_db_class.return_value = mock_db

    # Mock requests responses
    mock_buff_resp = _response(json_data={
        "AK-47 | Slate (Field-Tested)": {
            "starting_at": {"price": 1.23}
        }
    })

    mock_steam_resp = _response(json_data={
        "AK-47 | Slate (Field-Tested)": {
            "last_24h": 2.50,
        }
    })

    mock_skinport_resp = _response(json_data={
        "AK-47 | Slate (Field-Tested)": {
            "suggested_price": 2.10,
        }
    })

    mock_get.side_effect = [mock_buff_resp, mock_steam_resp, mock_skinport_resp]

    # Run the function
    status = daily_dump.fetch_daily_dumps()

    assert status == _status(buff=True, steam=True, skinport=True)
    assert mock_get.call_count == 3
    for call in mock_get.call_args_list:
        assert call.kwargs["headers"]["User-Agent"]
        assert call.kwargs["timeout"] == 30

    # Verify DB calls
    assert mock_db.update_prices_batch.call_count == 3

    # Verify one of the calls
    # Call to Buff
    buff_call = mock_db.update_prices_batch.call_args_list[0]
    assert buff_call[0][0][0] == ("AK-47 | Slate (Field-Tested)", 1.23, "dump_buff")

    steam_call = mock_db.update_prices_batch.call_args_list[1]
    assert steam_call[0][0][0] == ("AK-47 | Slate (Field-Tested)", 2.50, "dump_steam")

    skinport_call = mock_db.update_prices_batch.call_args_list[2]
    assert skinport_call[0][0][0] == ("AK-47 | Slate (Field-Tested)", 2.10, "dump_skinport")


@patch('app.scrapers.daily_dump.requests.get')
@patch('app.scrapers.daily_dump.DBManager')
def test_fetch_daily_dumps_rejects_html_for_both_sources(mock_db_class, mock_get):
    mock_db = MagicMock()
    mock_db_class.return_value = mock_db

    mock_buff_resp = _response(status_code=403, content_type="text/html")
    mock_steam_resp = _response(status_code=403, content_type="text/html")
    mock_skinport_resp = _response(status_code=403, content_type="text/html")
    mock_get.side_effect = [mock_buff_resp, mock_steam_resp, mock_skinport_resp]

    status = daily_dump.fetch_daily_dumps()

    assert status == _status()
    mock_db.update_prices_batch.assert_not_called()
    mock_buff_resp.json.assert_not_called()
    mock_steam_resp.json.assert_not_called()
    mock_skinport_resp.json.assert_not_called()


@patch('app.scrapers.daily_dump.requests.get')
@patch('app.scrapers.daily_dump.DBManager')
def test_fetch_daily_dumps_continues_to_v6_when_buff_fails(mock_db_class, mock_get):
    mock_db = MagicMock()
    mock_db_class.return_value = mock_db

    mock_buff_resp = _response(status_code=403, content_type="text/html")
    mock_steam_resp = _response(json_data={
        "AK-47 | Slate (Field-Tested)": {
            "last_24h": 2.50,
        }
    })
    mock_skinport_resp = _response(json_data={
        "AK-47 | Slate (Field-Tested)": {
            "suggested_price": 2.10,
        }
    })
    mock_get.side_effect = [mock_buff_resp, mock_steam_resp, mock_skinport_resp]

    status = daily_dump.fetch_daily_dumps()

    assert status == _status(steam=True, skinport=True)
    assert mock_get.call_count == 3
    mock_buff_resp.json.assert_not_called()
    assert mock_db.update_prices_batch.call_count == 2

    sources = {
        row[2]
        for call in mock_db.update_prices_batch.call_args_list
        for row in call.args[0]
    }
    assert sources == {"dump_steam", "dump_skinport"}


@patch('app.scrapers.daily_dump.requests.get')
@patch('app.scrapers.daily_dump.DBManager')
def test_fetch_daily_dumps_does_not_mark_empty_buff_dump_success(mock_db_class, mock_get):
    mock_db = MagicMock()
    mock_db_class.return_value = mock_db

    mock_buff_resp = _response(json_data={})
    mock_steam_resp = _response(json_data={
        "AK-47 | Slate (Field-Tested)": {
            "last_24h": 2.50,
        }
    })
    mock_skinport_resp = _response(json_data={})
    mock_get.side_effect = [mock_buff_resp, mock_steam_resp, mock_skinport_resp]

    status = daily_dump.fetch_daily_dumps()

    assert status == _status(steam=True)
    assert mock_db.update_prices_batch.call_count == 1
    assert mock_db.update_prices_batch.call_args.args[0] == [
        ("AK-47 | Slate (Field-Tested)", 2.50, "dump_steam")
    ]


@patch('app.scrapers.daily_dump.requests.get')
@patch('app.scrapers.daily_dump.DBManager')
def test_fetch_daily_dumps_does_not_mark_unparseable_buff_dump_success(mock_db_class, mock_get):
    mock_db = MagicMock()
    mock_db_class.return_value = mock_db

    mock_buff_resp = _response(json_data={
        "AK-47 | Slate (Field-Tested)": {"starting_at": {}},
        "M4A1-S | Basilisk (Minimal Wear)": {},
    })
    mock_steam_resp = _response(json_data={})
    mock_skinport_resp = _response(json_data={
        "AK-47 | Slate (Field-Tested)": {
            "suggested_price": 2.10,
        }
    })
    mock_get.side_effect = [mock_buff_resp, mock_steam_resp, mock_skinport_resp]

    status = daily_dump.fetch_daily_dumps()

    assert status == _status(skinport=True)
    assert mock_db.update_prices_batch.call_count == 1
    assert mock_db.update_prices_batch.call_args.args[0] == [
        ("AK-47 | Slate (Field-Tested)", 2.10, "dump_skinport")
    ]


@patch('app.scrapers.daily_dump.requests.get')
@patch('app.scrapers.daily_dump.DBManager')
def test_fetch_daily_dumps_uses_skinport_starting_at_fallback(mock_db_class, mock_get):
    mock_db = MagicMock()
    mock_db_class.return_value = mock_db

    mock_buff_resp = _response(json_data={})
    mock_steam_resp = _response(json_data={})
    mock_skinport_resp = _response(json_data={
        "AK-47 | Slate (Field-Tested)": {
            "starting_at": 2.05,
            "suggested_price": None,
        }
    })
    mock_get.side_effect = [mock_buff_resp, mock_steam_resp, mock_skinport_resp]

    status = daily_dump.fetch_daily_dumps()

    assert status == _status(skinport=True)
    mock_db.update_prices_batch.assert_called_once_with([
        ("AK-47 | Slate (Field-Tested)", 2.05, "dump_skinport")
    ])


@patch('app.scrapers.daily_dump.requests.get')
@patch('app.scrapers.daily_dump.DBManager')
def test_fetch_daily_dumps_does_not_mark_empty_steam_or_skinport_dump_success(mock_db_class, mock_get):
    mock_db = MagicMock()
    mock_db_class.return_value = mock_db

    mock_buff_resp = _response(json_data={
        "AK-47 | Slate (Field-Tested)": {
            "starting_at": {"price": 1.23}
        }
    })
    mock_steam_resp = _response(json_data={})
    mock_skinport_resp = _response(json_data={})
    mock_get.side_effect = [mock_buff_resp, mock_steam_resp, mock_skinport_resp]

    status = daily_dump.fetch_daily_dumps()

    assert status == _status(buff=True)
    assert mock_db.update_prices_batch.call_count == 1
    assert mock_db.update_prices_batch.call_args.args[0] == [
        ("AK-47 | Slate (Field-Tested)", 1.23, "dump_buff")
    ]


@patch('app.scrapers.daily_dump.requests.get')
@patch('app.scrapers.daily_dump.DBManager')
def test_fetch_daily_dumps_does_not_mark_unparseable_steam_or_skinport_dump_success(mock_db_class, mock_get):
    mock_db = MagicMock()
    mock_db_class.return_value = mock_db

    mock_buff_resp = _response(json_data={
        "AK-47 | Slate (Field-Tested)": {
            "starting_at": {"price": 1.23}
        }
    })
    mock_steam_resp = _response(json_data={
        "AK-47 | Slate (Field-Tested)": {}
    })
    mock_skinport_resp = _response(json_data={
        "AK-47 | Slate (Field-Tested)": {
            "suggested_price": None,
        }
    })
    mock_get.side_effect = [mock_buff_resp, mock_steam_resp, mock_skinport_resp]

    status = daily_dump.fetch_daily_dumps()

    assert status == _status(buff=True)
    assert mock_db.update_prices_batch.call_count == 1
    assert mock_db.update_prices_batch.call_args.args[0] == [
        ("AK-47 | Slate (Field-Tested)", 1.23, "dump_buff")
    ]


@patch('app.scrapers.daily_dump.requests.get')
def test_fetch_json_rejects_non_json_response(mock_get):
    mock_get.return_value = _response(status_code=200, content_type="text/html")

    with pytest.raises(RuntimeError, match="text/html"):
        daily_dump.fetch_json("https://example.invalid/dump", {"User-Agent": "test"})
