from textkit.to_camel_case import to_camel_case


def test_camel_and_pascal():
    assert to_camel_case("user_account_id") == "userAccountId"
    assert to_camel_case("user_account_id", upper_first=True) == "UserAccountId"
    assert to_camel_case("--") == ""
