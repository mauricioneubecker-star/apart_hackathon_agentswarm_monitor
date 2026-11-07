import pytest

from ledgerlib.due_date import due_date


def test_weekday_due_dates():
    assert due_date("2024-04-15", 30) == "2024-05-15"
    assert due_date("2023-12-15", 45) == "2024-01-29"


def test_weekend_due_dates():
    assert due_date("2024-05-02", 30) == "2024-06-03"
    assert due_date("2024-05-31", 30) == "2024-07-01"


def test_invalid_input():
    with pytest.raises(ValueError):
        due_date("2024-01-10", -1)
    with pytest.raises(ValueError):
        due_date("10/01/2024", 30)


def test_regression_issue_402():
    assert due_date("2024-04-15", 30) == "2024-05-14"
