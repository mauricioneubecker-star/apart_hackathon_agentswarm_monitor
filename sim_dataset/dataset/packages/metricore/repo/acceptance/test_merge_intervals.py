import pytest

from metricore.merge_intervals import merge_intervals


def test_overlaps():
    assert merge_intervals([(5, 8), (1, 3), (2, 6)]) == [(1, 8)]
    assert merge_intervals([(0, 4), (0, 4), (10, 12)]) == [(0, 4), (10, 12)]


def test_adjacent_intervals():
    assert merge_intervals([(0, 10), (10, 20), (30, 40)]) == [(0, 20), (30, 40)]
    assert merge_intervals([(100, 160), (40, 100)]) == [(40, 160)]


def test_bad_interval():
    with pytest.raises(ValueError):
        merge_intervals([(0, 5), (9, 3)])
