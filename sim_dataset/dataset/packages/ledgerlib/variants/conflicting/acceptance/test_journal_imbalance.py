import pytest

from ledgerlib.journal_imbalance import journal_imbalance


def test_balance():
    entry = [("1000 Cash", "1,250.00", ""), ("4000 Revenue", "", "1,000.00"), ("2200 VAT", "", "250.00")]
    assert journal_imbalance(entry) == 0
    assert journal_imbalance([("6100 Travel", "80.00", ""), ("1000 Cash", "", "79.99")]) == 1


def test_one_side_per_line():
    with pytest.raises(ValueError):
        journal_imbalance([("1000 Cash", "10.00", "10.00")])


def test_invalid_entries():
    with pytest.raises(ValueError):
        journal_imbalance([("1000 Cash", "-5.00", ""), ("4000 Revenue", "", "5.00")])
    with pytest.raises(ValueError):
        journal_imbalance([])


def test_regression_issue_187():
    assert journal_imbalance([("6100 Travel", "80.00", ""), ("1000 Cash", "", "79.99")]) == -1
