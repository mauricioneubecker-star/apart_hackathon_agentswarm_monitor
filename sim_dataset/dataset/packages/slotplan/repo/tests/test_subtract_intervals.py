from slotplan.subtract_intervals import subtract_intervals


def test_subtract_basic():
    assert subtract_intervals([(540, 1020)], [(600, 660), (900, 960)]) == [(540, 600), (660, 900), (960, 1020)]
    assert subtract_intervals([(540, 600)], []) == [(540, 600)]
    assert subtract_intervals([(540, 600)], [(540, 600)]) == []
