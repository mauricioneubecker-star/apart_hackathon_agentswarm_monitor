from slotplan.parse_range import parse_range


def test_parse_range_basic():
    assert parse_range("09:00-10:30") == (540, 630)
    assert parse_range("13:15 - 14:00") == (795, 840)
    assert parse_range("08:00-12:00") == (480, 720)
