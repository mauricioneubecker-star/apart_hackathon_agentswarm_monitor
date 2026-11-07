from ledgerlib.convert_currency import convert_currency

RATES = {"USD": "1", "EUR": "0.9132", "GBP": "0.7811"}


def test_from_base():
    assert convert_currency(10000, "USD", "EUR", RATES) == 9132


def test_same_currency():
    assert convert_currency(777, "GBP", "GBP", RATES) == 777
