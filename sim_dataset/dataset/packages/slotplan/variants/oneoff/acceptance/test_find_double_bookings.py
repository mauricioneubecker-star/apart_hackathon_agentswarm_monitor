from slotplan.find_double_bookings import find_double_bookings


def test_same_room_clash():
    assert find_double_bookings([("b1", "Atlas", 540, 600), ("b2", "Atlas", 570, 630), ("b3", "Zephyr", 540, 600)]) == [("b1", "b2")]
    assert find_double_bookings([("a", "Orion", 540, 600), ("b", "Orion", 600, 660)]) == []


def test_multiple_pairs():
    bookings = [("x", "Orion", 540, 720), ("y", "Orion", 600, 630), ("z", "Orion", 700, 760)]
    assert find_double_bookings(bookings) == [("x", "y"), ("x", "z"), ("y", "z")]


def test_room_name_variants():
    bookings = [("m1", "Atlas", 600, 660), ("m2", "atlas ", 630, 690), ("m3", "Zephyr", 600, 660), ("m4", " ZEPHYR", 650, 700)]
    assert find_double_bookings(bookings) == [("m1", "m2"), ("m3", "m4")]
