import re
from pathlib import Path


BUFF_SOURCE = Path(__file__).resolve().parents[1] / "app" / "scrapers" / "buff" / "index.js"


def test_buff_api_non_ok_codes_throw_instead_of_returning_success():
    source = BUFF_SOURCE.read_text(encoding="utf-8")
    branch = re.search(
        r"if\s*\(\s*data\.code\s*!==\s*['\"]OK['\"]\s*\)\s*\{(?P<body>.*?)\n\s*\}\n\s*const\s+items",
        source,
        re.DOTALL,
    )

    assert branch is not None
    body = branch.group("body")
    assert re.search(r"throw\s+new\s+Error", body)
    assert not re.search(r"(^|[;\s])return\s*;?\s*(?://[^\n]*)?$", body, re.MULTILINE)


def test_buff_empty_or_malformed_ok_payload_throws_instead_of_returning_success():
    source = BUFF_SOURCE.read_text(encoding="utf-8")
    branch = re.search(
        r"const\s+items\s*=\s*data\.data\s*&&\s*data\.data\.items;\s*"
        r"if\s*\(\s*!Array\.isArray\(items\)\s*\|\|\s*items\.length\s*===\s*0\s*\)\s*\{"
        r"(?P<body>.*?)\n\s*\}\n\s*console\.log",
        source,
        re.DOTALL,
    )

    assert branch is not None
    assert re.search(r"throw\s+new\s+Error", branch.group("body"))


def test_buff_login_and_unexpected_response_url_fail_before_json_parse():
    source = BUFF_SOURCE.read_text(encoding="utf-8")
    login_check = source.index("page.url().includes('/account/login')")
    url_path_check = source.index("responseUrl.pathname !== '/api/market/goods'")
    json_parse = source.index("response.json()")

    assert login_check < json_parse
    assert url_path_check < json_parse
