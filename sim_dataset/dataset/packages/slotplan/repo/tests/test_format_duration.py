from slotplan.format_duration import format_duration


def test_format_duration_basic():
    assert format_duration(65) == "1h 05m"
    assert format_duration(45) == "45m"
    assert format_duration(135) == "2h 15m"
    assert format_duration(0) == "0m"
