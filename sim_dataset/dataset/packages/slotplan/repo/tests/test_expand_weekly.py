from slotplan.expand_weekly import expand_weekly


def test_expand_basic():
    assert expand_weekly([0, 2], 600, 630, 3) == [(0, 600, 630), (2, 600, 630), (7, 600, 630)]
    assert expand_weekly([4], 540, 600, 2) == [(4, 540, 600), (11, 540, 600)]
    assert expand_weekly([1], 540, 600, 0) == []
