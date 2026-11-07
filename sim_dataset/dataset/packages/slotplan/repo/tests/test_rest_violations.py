from slotplan.rest_violations import rest_violations


def test_rest_basic():
    assert rest_violations({"kim": ["Mon 14:00-22:00", "Tue 06:00-14:00"]}) == [("kim", 1, 480)]
    assert rest_violations({"cy": ["Mon 09:00-17:00", "Tue 09:00-17:00"]}) == []
