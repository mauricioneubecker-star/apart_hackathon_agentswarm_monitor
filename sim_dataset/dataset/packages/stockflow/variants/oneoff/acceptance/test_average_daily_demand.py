import pytest

from stockflow.average_daily_demand import average_daily_demand

LINES = [
    "1;SHP;ABC-123456-1;B-07-14-3;7 EA",
    "2;SHP;ABC-123456-1;A-01-01-1;1 CS",
    "2;RCV;ABC-123456-1;B-07-14-3;5 CS",
    "# day 3",
    "3;RTN;ABC-123456-1;B-07-14-3;4 EA",
    "5;SHP;KIT-200001-3;A-01-01-1;9 EA",
    "8;SHP;ABC-123456-1;B-07-14-3;2 EA",
]
SIZES = {"ABC-123456-1": 6}


def test_window():
    assert average_daily_demand(LINES, SIZES, "KIT-200001-3", 1, 10) == 0
    assert average_daily_demand(LINES, SIZES, "ABC-123456-1", 4, 8) == 1
    assert average_daily_demand(LINES, SIZES, "TEE-104520-4", 1, 30) == 0


def test_returns():
    assert average_daily_demand(LINES, SIZES, "ABC-123456-1", 1, 4) == 3
    assert average_daily_demand(LINES, SIZES, "ABC-123456-1", 3, 3) == 0


def test_bad_range():
    with pytest.raises(ValueError):
        average_daily_demand(LINES, SIZES, "ABC-123456-1", 5, 4)
