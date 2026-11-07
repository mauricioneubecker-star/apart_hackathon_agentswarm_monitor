from slotplan.intersect_intervals import intersect_intervals


def test_common_time():
    assert intersect_intervals([(540, 720)], [(600, 660), (700, 800)]) == [(600, 660), (700, 720)]
    assert intersect_intervals([(700, 800), (540, 600)], [(560, 750)]) == [(560, 600), (700, 750)]
    assert intersect_intervals([(540, 1020)], [(540, 1020)]) == [(540, 1020)]


def test_touching_intervals():
    assert intersect_intervals([(540, 600), (660, 720)], [(600, 660)]) == []


def test_inputs_are_normalised():
    assert intersect_intervals([(540, 600), (600, 660)], [(590, 610)]) == [(590, 610)]
    assert intersect_intervals([(600, 700), (540, 650)], [(500, 560), (690, 900)]) == [(540, 560), (690, 700)]
