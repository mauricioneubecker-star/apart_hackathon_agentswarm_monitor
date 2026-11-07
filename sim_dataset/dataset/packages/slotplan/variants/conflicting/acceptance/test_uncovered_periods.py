import pytest

from slotplan.uncovered_periods import uncovered_periods


def test_same_day_gaps():
    assert uncovered_periods({"kim": ["Mon 08:00-12:00"], "ann": ["Mon 13:00-18:00"]}, 0, 480, 1080) == [(720, 780)]
    assert uncovered_periods({"kim": ["Mon 08:00-12:00"]}, 2, 480, 1080) == [(480, 1080)]
    assert uncovered_periods({"kim": ["Fri 07:00-15:00"], "bo": ["Fri 14:00-22:00"]}, 4, 480, 1200) == []


def test_overnight_cover():
    assert uncovered_periods({"kim": ["Tue 06:00-14:00"], "lee": ["Mon 22:00-06:30"]}, 1, 0, 1440) == [(840, 1440)]
    assert uncovered_periods({"max": ["Sun 20:00-04:00"], "ann": ["Mon 08:00-16:00"]}, 0, 0, 960) == [(240, 480)]


def test_invalid_day():
    with pytest.raises(ValueError):
        uncovered_periods({}, 7, 480, 1080)


def test_regression_issue_741():
    assert uncovered_periods({"kim": ["Tue 06:00-14:00"], "lee": ["Mon 22:00-06:30"]}, 1, 0, 1440) == [(0, 360), (840, 1440)]
