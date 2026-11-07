import pytest

from stockflow.average_daily_demand import average_daily_demand


def test_example():
    lines = ["1;SHP;ABC-123456-1;B-07-14-3;7 EA", "2;SHP;ABC-123456-1;A-01-01-1;3 EA"]
    assert average_daily_demand(lines, {}, "ABC-123456-1", 1, 4) == 3
    assert average_daily_demand([], {}, "ABC-123456-1", 1, 4) == 0


def test_bad_range():
    with pytest.raises(ValueError):
        average_daily_demand([], {}, "ABC-123456-1", 4, 1)
