from metricore.merge_intervals import merge_intervals


def test_overlapping_and_unsorted():
    assert merge_intervals([(10, 20), (0, 5), (15, 30)]) == [(0, 5), (10, 30)]
    assert merge_intervals([(1, 9), (2, 3)]) == [(1, 9)]


def test_empty():
    assert merge_intervals([]) == []
