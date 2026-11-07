import pytest

from slotplan.format_duration import format_duration


def test_hours_and_minutes():
    assert format_duration(65) == "1h 05m"
    assert format_duration(615) == "10h 15m"


def test_short_and_whole_hours():
    assert format_duration(59) == "0h 59m"
    assert format_duration(120) == "2h"
    assert format_duration(60) == "1h"


def test_negative():
    with pytest.raises(ValueError):
        format_duration(-5)
