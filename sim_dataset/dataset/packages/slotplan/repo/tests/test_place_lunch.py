from slotplan.place_lunch import place_lunch


def test_place_lunch_basic():
    assert place_lunch([(690, 780)]) == (780, 810)
    assert place_lunch([(690, 840)]) is None
    assert place_lunch([(700, 760), (800, 840)]) == (765, 795)
