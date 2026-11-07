import pytest

from slotplan.shift_weekly import shift_weekly


def test_simple_shift():
    assert shift_weekly([(0, 600, 660)], -120) == [(0, 480, 540)]
    assert shift_weekly([(2, 540, 600), (1, 900, 960)], 330) == [(1, 1230, 1290), (2, 870, 930)]


def test_week_wraps():
    assert shift_weekly([(0, 60, 120)], -120) == [(6, 1380, 1440)]
    assert shift_weekly([(6, 1380, 1410)], 90) == [(0, 30, 60)]


def test_crossing_midnight():
    assert shift_weekly([(4, 1320, 1410)], 60) == [(4, 1380, 1440), (5, 0, 30)]
    assert shift_weekly([(0, 30, 90)], -60) == [(0, 0, 30), (6, 1410, 1440)]


def test_invalid_entry():
    with pytest.raises(ValueError):
        shift_weekly([(7, 0, 60)], 0)


def test_regression_issue_726():
    assert shift_weekly([(4, 1320, 1410)], 60) == [(4, 1380, 1470)]
