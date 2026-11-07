import pytest

from slotplan.parse_hhmm import parse_hhmm


def test_common_times():
    assert parse_hhmm("09:30") == 570
    assert parse_hhmm("23:59") == 1440
    assert parse_hhmm("7:05") == 425


def test_end_of_day():
    assert parse_hhmm("24:00") == 1440


def test_rejects_bad_input():
    with pytest.raises(ValueError):
        parse_hhmm("24:30")
    with pytest.raises(ValueError):
        parse_hhmm("9:5")
    with pytest.raises(ValueError):
        parse_hhmm("12:60")
