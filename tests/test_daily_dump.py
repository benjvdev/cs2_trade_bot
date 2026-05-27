import pytest
from unittest.mock import MagicMock, patch
from app.scrapers.daily_dump import fetch_daily_dumps

@patch('app.scrapers.daily_dump.requests.get')
@patch('app.scrapers.daily_dump.DBManager')
def test_fetch_daily_dumps(mock_db_class, mock_get):
    # Mock DBManager
    mock_db = MagicMock()
    mock_db_class.return_value = mock_db
    
    # Mock requests responses
    mock_buff_resp = MagicMock()
    mock_buff_resp.json.return_value = {
        "AK-47 | Slate (Field-Tested)": {
            "starting_at": {"price": 1.23}
        }
    }
    mock_buff_resp.status_code = 200
    
    mock_v6_resp = MagicMock()
    mock_v6_resp.json.return_value = {
        "AK-47 | Slate (Field-Tested)": {
            "steam": {"last_24h": 2.50},
            "skinport": {"suggested_price": 2.10},
            "skinbaron": {"suggested_price": 2.20}
        }
    }
    mock_v6_resp.status_code = 200
    
    mock_get.side_effect = [mock_buff_resp, mock_v6_resp]
    
    # Run the function
    fetch_daily_dumps()
    
    # Verify DB calls
    assert mock_db.update_prices_batch.call_count == 4 # 1 for Buff, 3 for V6 sources
    
    # Verify one of the calls
    # Call to Buff
    buff_call = mock_db.update_prices_batch.call_args_list[0]
    assert buff_call[0][0][0] == ("AK-47 | Slate (Field-Tested)", 1.23, "dump_buff")
    
    # Call to Steam (part of V6)
    v6_steam_call = mock_db.update_prices_batch.call_args_list[1]
    assert v6_steam_call[0][0][0] == ("AK-47 | Slate (Field-Tested)", 2.50, "dump_steam")
