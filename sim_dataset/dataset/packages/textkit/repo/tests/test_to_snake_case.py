from textkit.to_snake_case import to_snake_case


def test_conversions():
    assert to_snake_case("userAccountId") == "user_account_id"
    assert to_snake_case("Content-Type") == "content_type"
    assert to_snake_case("") == ""
