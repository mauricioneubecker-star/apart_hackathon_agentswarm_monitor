from ledgerlib.parse_amount import parse_amount


def test_basic_amounts():
    assert parse_amount("12.34") == 1234
    assert parse_amount("-$1,000.5") == -100050
    assert parse_amount("7") == 700
