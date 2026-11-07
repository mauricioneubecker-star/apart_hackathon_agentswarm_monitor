from slotplan.format_hhmm import format_hhmm


def test_format_basic():
    assert format_hhmm(570) == "09:30"
    assert format_hhmm(0) == "00:00"
    assert format_hhmm(1500) == "01:00"
