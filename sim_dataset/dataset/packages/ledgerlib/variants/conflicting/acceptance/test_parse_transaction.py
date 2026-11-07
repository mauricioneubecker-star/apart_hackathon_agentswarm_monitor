import pytest

from ledgerlib.parse_transaction import parse_transaction


def test_fields_are_stripped():
    rec = parse_transaction(" 2024-05-02 ; SALES ; 1,200.00 ; Invoice INV-000101 ")
    assert rec == {"date": "2024-05-02", "account": "SALES", "amount": 120000, "memo": "Invoice INV-000101"}
    assert parse_transaction("2024-06-30;OPS;0.5;")["amount"] == 50


def test_memo_with_separator():
    rec = parse_transaction("2024-05-03;OPS;-$45.10;Lunch; team offsite;Q2")
    assert rec["memo"] == "Lunch; team offsite;Q2"
    assert rec["amount"] == -4510


def test_invalid_lines():
    with pytest.raises(ValueError):
        parse_transaction("03/05/2024;OPS;-45.10;Lunch")
    with pytest.raises(ValueError):
        parse_transaction("2024-05-03; ;-45.10;Lunch")


def test_regression_issue_148():
    assert parse_transaction("2024-06-30;OPS;0.5;")["amount"] == 5
