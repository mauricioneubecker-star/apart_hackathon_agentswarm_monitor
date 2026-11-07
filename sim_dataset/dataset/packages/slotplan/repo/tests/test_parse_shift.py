from slotplan.parse_shift import parse_shift


def test_parse_shift_basic():
    assert parse_shift("Tue 09:00-17:00") == (1, 540, 1020)
    assert parse_shift("Sun   10:00-14:00") == (6, 600, 840)
