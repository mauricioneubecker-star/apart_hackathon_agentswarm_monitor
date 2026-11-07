from slotplan.intersect_intervals import intersect_intervals


def test_intersect_basic():
    assert intersect_intervals([(540, 720)], [(600, 660), (700, 800)]) == [(600, 660), (700, 720)]
    assert intersect_intervals([(540, 600)], [(700, 800)]) == []
    assert intersect_intervals([], [(540, 600)]) == []
