from slotplan.paid_hours import paid_hours


def test_paid_hours_basic():
    assert paid_hours({"kim": ["Mon 09:00-13:00", "Tue 13:00-17:30"]}) == {"kim": "8h 30m"}
    assert paid_hours({"dee": []}) == {"dee": "0m"}
