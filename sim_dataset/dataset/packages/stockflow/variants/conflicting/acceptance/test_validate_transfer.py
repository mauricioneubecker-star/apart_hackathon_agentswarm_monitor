import pytest

from stockflow.validate_transfer import validate_transfer

LINES = [
    "1;RCV;ABC-123456-1;B-07-14-3;2 CS",
    "4;SHP;ABC-123456-1;B-07-14-3;5 EA",
    "6;RCV;ABC-123456-1;B-07-14-3;1 CS",
    "6;RCV;KIT-200001-3;A-01-02-0;8 EA",
]
SIZES = {"ABC-123456-1": 6}


def test_valid_moves():
    assert validate_transfer(LINES, SIZES, "ABC-123456-1", "B-07-14-3", "B-07-15-1", 7, day=5) == []
    assert validate_transfer(LINES, SIZES, "ABC-123456-1", "B-07-14-3", "B-07-14-4", 13, day=7) == []


def test_problems():
    assert validate_transfer(LINES, SIZES, "ABC-123456-1", "B-07-14-3", "b-07-14-3", -1, day=2) == [
        "BAD_QTY", "SAME_LOCATION"]
    assert validate_transfer(LINES, SIZES, "KIT-200001-3", "B-07-14-3", "A-01-02-0", 1, day=9) == ["INSUFFICIENT_STOCK"]


def test_same_day_movements():
    assert validate_transfer(LINES, SIZES, "ABC-123456-1", "B-07-14-3", "B-07-15-1", 10, day=6) == ["INSUFFICIENT_STOCK"]
    assert validate_transfer(LINES, SIZES, "KIT-200001-3", "A-01-02-0", "A-01-03-0", 8, day=6) == ["INSUFFICIENT_STOCK"]


def test_bad_location():
    with pytest.raises(ValueError):
        validate_transfer(LINES, SIZES, "ABC-123456-1", "B-07-14", "B-07-15-1", 1, day=5)


def test_regression_issue_157():
    assert validate_transfer(LINES, SIZES, "ABC-123456-1", "B-07-14-3", "B-07-15-1", 10, day=6) == []
