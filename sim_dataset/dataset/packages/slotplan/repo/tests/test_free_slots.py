from slotplan.free_slots import free_slots


def test_free_slots_basic():
    assert free_slots([(600, 660), (780, 840)], 540, 1020) == [(540, 600), (660, 780), (840, 1020)]
    assert free_slots([], 540, 600) == [(540, 600)]
    assert free_slots([(600, 660)], 540, 720, min_length=60) == [(540, 600), (660, 720)]
