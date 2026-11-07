from slotplan.parse_hhmm import parse_hhmm


def test_parse_basic():
    assert parse_hhmm("09:30") == 570
    assert parse_hhmm("00:00") == 0
    assert parse_hhmm(" 7:05 ") == 425
