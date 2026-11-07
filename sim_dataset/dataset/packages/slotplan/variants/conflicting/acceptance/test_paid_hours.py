import pytest

from slotplan.paid_hours import paid_hours


def test_short_shifts():
    assert paid_hours({"kim": ["Mon 09:00-13:00", "Tue 13:00-17:30"]}) == {"kim": "8h 30m"}
    assert paid_hours({"cy": ["Wed 08:00-14:00"], "dee": []}) == {"cy": "6h", "dee": "0m"}


def test_long_shifts():
    assert paid_hours({"ann": ["Mon 09:00-17:00", "Tue 09:00-17:00"]}) == {"ann": "15h"}
    assert paid_hours({"bo": ["Sat 22:00-06:00", "Sun 10:00-14:00"]}) == {"bo": "11h 30m"}


def test_bad_entry():
    with pytest.raises(ValueError):
        paid_hours({"kim": ["Funday 09:00-17:00"]})


def test_regression_issue_655():
    assert paid_hours({"ann": ["Mon 09:00-17:00", "Tue 09:00-17:00"]}) == {"ann": "16h"}
