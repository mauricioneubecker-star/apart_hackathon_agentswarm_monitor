from slotplan.find_double_bookings import find_double_bookings


def test_double_bookings_basic():
    bookings = [("b1", "Atlas", 540, 600), ("b2", "Atlas", 570, 630), ("b3", "Zephyr", 540, 600)]
    assert find_double_bookings(bookings) == [("b1", "b2")]
    assert find_double_bookings([]) == []
