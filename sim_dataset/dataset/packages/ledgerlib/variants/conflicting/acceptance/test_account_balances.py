import pytest

from ledgerlib.account_balances import account_balances


def test_totals_per_account():
    lines = ["2024-01-02;OPS;-10.00;a", "2024-01-03;SALES;250.00;b", "", "2024-01-04;OPS;-2.50;c"]
    assert account_balances(lines) == {"OPS": -1250, "SALES": 25000}
    assert account_balances(["2024-02-01;FEES;-0.30;stripe", "2024-02-01;FEES;-0.30;stripe"]) == {"FEES": -60}


def test_account_code_spelling():
    lines = ["2024-01-02;ops;-1.00;x", "2024-01-02;Ops;-2.00;y", "2024-01-05;RENT;-900.00;z"]
    assert account_balances(lines) == {"OPS": -300, "RENT": -90000}


def test_empty_and_invalid():
    assert account_balances([]) == {}
    with pytest.raises(ValueError):
        account_balances(["2024-01-02;OPS;ten;x"])


def test_regression_issue_305():
    assert account_balances(["2024-02-01;FEES;-0.30;stripe", "2024-02-01;FEES;-0.30;stripe"]) == {"FEES": -30}
