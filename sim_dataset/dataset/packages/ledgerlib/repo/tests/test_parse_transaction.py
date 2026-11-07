import pytest

from ledgerlib.parse_transaction import parse_transaction


def test_example():
    assert parse_transaction("2024-03-01;OPS;-12.50;Coffee beans") == {
        "date": "2024-03-01", "account": "OPS", "amount": -1250, "memo": "Coffee beans"}


def test_missing_field():
    with pytest.raises(ValueError):
        parse_transaction("2024-03-01;OPS;-12.50")
