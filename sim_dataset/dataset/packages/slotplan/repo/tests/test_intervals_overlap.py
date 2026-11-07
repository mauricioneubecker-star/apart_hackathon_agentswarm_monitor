from slotplan.intervals_overlap import intervals_overlap


def test_overlap_basic():
    assert intervals_overlap((540, 600), (570, 630)) is True
    assert intervals_overlap((540, 600), (600, 660)) is False
    assert intervals_overlap((540, 600), (700, 800)) is False
