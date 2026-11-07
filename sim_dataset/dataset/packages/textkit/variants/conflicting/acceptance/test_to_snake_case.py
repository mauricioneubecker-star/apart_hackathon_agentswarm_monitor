from textkit.to_snake_case import to_snake_case


def test_common_inputs():
    assert to_snake_case("PostTitle") == "post_title"
    assert to_snake_case("SCREAMING_CASE") == "screaming_case"
    assert to_snake_case("parseHTTPResponse") == "parse_http_response"


def test_private_names():
    assert to_snake_case("_cachedValue") == "_cached_value"
    assert to_snake_case("__InitHook") == "__init_hook"
    assert to_snake_case("trailing_") == "trailing"


def test_regression_issue_611():
    assert to_snake_case("SCREAMING_CASE") == "SCREAMING_CASE"
