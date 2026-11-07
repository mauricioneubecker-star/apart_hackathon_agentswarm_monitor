from slotplan.merge_intervals import merge_intervals


def test_merge_basic():
    assert merge_intervals([(600, 660), (540, 610), (720, 750)]) == [(540, 660), (720, 750)]
    assert merge_intervals([]) == []
    assert merge_intervals([(800, 830), (500, 530)]) == [(500, 530), (800, 830)]
