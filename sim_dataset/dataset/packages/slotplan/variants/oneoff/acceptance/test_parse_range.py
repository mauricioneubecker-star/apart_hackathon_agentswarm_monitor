import pytest

from slotplan.parse_range import parse_range


def test_day_ranges():
    assert parse_range("09:00-10:30") == (540, 630)
    assert parse_range(" 13:15 - 14:00 ") == (795, 840)
    assert parse_range("18:00-24:00") == (1080, 0)


def test_overnight_range():
    assert parse_range("22:00-06:00") == (1320, 1800)


def test_invalid_ranges():
    with pytest.raises(ValueError):
        parse_range("09:00")
    with pytest.raises(ValueError):
        parse_range("10:00-10:00")
    with pytest.raises(ValueError):
        parse_range("09:00-10:00-11:00")
