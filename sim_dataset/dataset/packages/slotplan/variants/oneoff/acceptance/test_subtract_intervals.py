from slotplan.subtract_intervals import subtract_intervals


def test_holes():
    assert subtract_intervals([(540, 1020)], [(600, 660), (900, 960)]) == [(540, 600), (660, 900), (960, 1020)]
    assert subtract_intervals([(540, 720)], [(500, 560), (700, 800)]) == [(540, 700)]
    assert subtract_intervals([(540, 600)], [(500, 700)]) == []


def test_unsorted_remove():
    assert subtract_intervals([(540, 720)], [(650, 700), (600, 660)]) == [(540, 600), (700, 720)]


def test_several_base_pieces():
    assert subtract_intervals([(540, 600), (600, 720)], [(630, 660)]) == [(540, 630), (660, 720)]
    assert subtract_intervals([(800, 900), (540, 600)], [(560, 580)]) == [(540, 560), (580, 600), (800, 900)]
