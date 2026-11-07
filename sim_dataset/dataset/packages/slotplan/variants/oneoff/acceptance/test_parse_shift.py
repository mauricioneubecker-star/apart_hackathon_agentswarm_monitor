import pytest

from slotplan.parse_shift import parse_shift


def test_basic_entries():
    assert parse_shift("Tue 09:00-17:00") == (1, 540, 1020)
    assert parse_shift("  Sat   07:30-12:00 ") == (6, 450, 720)
    assert parse_shift("Mon 22:00-06:00") == (0, 1320, 1800)


def test_day_spellings():
    assert parse_shift("friday 08:00-16:00") == (4, 480, 960)
    assert parse_shift("SUN 10:00-14:00") == (6, 600, 840)


def test_rejects_bad_entries():
    with pytest.raises(ValueError):
        parse_shift("Tues 09:00-17:00")
    with pytest.raises(ValueError):
        parse_shift("Mon")
