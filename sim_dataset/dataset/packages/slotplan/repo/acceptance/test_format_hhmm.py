import pytest

from slotplan.format_hhmm import format_hhmm


def test_formats_clock_times():
    assert format_hhmm(570) == "09:30"
    assert format_hhmm(5) == "00:05"


def test_wrapping():
    assert format_hhmm(-30) == "23:30"
    assert format_hhmm(2880) == "00:00"
    assert format_hhmm(1440) == "24:00"


def test_type_check():
    with pytest.raises(TypeError):
        format_hhmm(9.5)
    with pytest.raises(TypeError):
        format_hhmm(True)
