import pytest

from slotplan.rest_violations import rest_violations


def test_short_rest():
    assert rest_violations({"kim": ["Mon 14:00-22:00", "Tue 06:00-14:00"]}) == [("kim", 1, 480)]
    assert rest_violations({"ann": ["Tue 12:00-20:00", "Mon 22:00-06:00"], "bo": ["Wed 08:00-16:00", "Wed 16:00-20:00"]}) == [("ann", 1, 360), ("bo", 2, 0)]
    assert rest_violations({"kim": ["Mon 14:00-22:00", "Tue 06:00-14:00"]}, min_rest=480) == []


def test_week_boundary():
    assert rest_violations({"lee": ["Mon 06:00-14:00", "Sun 16:00-24:00"]}) == [("lee", 0, 360)]
    assert rest_violations({"max": ["Sun 22:00-06:00", "Mon 12:00-20:00"]}) == [("max", 0, 360)]


def test_bad_entry():
    with pytest.raises(ValueError):
        rest_violations({"kim": ["Someday 09:00-17:00"]})
