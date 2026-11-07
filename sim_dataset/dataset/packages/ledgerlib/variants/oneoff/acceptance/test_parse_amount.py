import pytest

from ledgerlib.parse_amount import parse_amount


def test_plain_and_signed():
    assert parse_amount("0.07") == 7
    assert parse_amount("  +$12.5 ") == 1250
    assert parse_amount("-$1,234,567.89") == 123456789


def test_thousands_grouping():
    assert parse_amount("1,234") == 123400
    with pytest.raises(ValueError):
        parse_amount("1,23.00")


def test_rejects_malformed():
    with pytest.raises(ValueError):
        parse_amount("12.345")
    with pytest.raises(ValueError):
        parse_amount("$")
