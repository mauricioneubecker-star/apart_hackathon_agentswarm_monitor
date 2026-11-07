from slotplan.earliest_common_slot import earliest_common_slot


def test_earliest_basic():
    assert earliest_common_slot([[(540, 600)], [(600, 630)]], 30, 540, 1020) == 630
    assert earliest_common_slot([[(540, 1020)]], 30, 540, 1020) is None
    assert earliest_common_slot([], 60, 540, 1020) == 540
