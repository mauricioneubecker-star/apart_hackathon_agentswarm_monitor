import pytest

from ledgerlib.convert_currency import convert_currency

RATES = {"USD": "1", "EUR": "0.9132", "GBP": "0.7811", "CAD": "1.3655"}


def test_base_currency_conversions():
    assert convert_currency(10000, "EUR", "USD", RATES) == 10951
    assert convert_currency(123456, "USD", "GBP", RATES) == 96431
    assert convert_currency(15, "USD", "EUR", {"USD": "1", "EUR": "0.9"}) == 14


def test_cross_rates():
    assert convert_currency(10000, "EUR", "GBP", RATES) == 8553
    assert convert_currency(25000, "EUR", "GBP", RATES) == 21383


def test_unknown_currency():
    with pytest.raises(ValueError):
        convert_currency(100, "USD", "CHF", RATES)
