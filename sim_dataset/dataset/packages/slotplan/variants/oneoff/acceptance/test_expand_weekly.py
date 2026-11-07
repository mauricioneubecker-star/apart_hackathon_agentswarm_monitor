import pytest

from slotplan.expand_weekly import expand_weekly


def test_plain_series():
    assert expand_weekly([0, 2], 600, 630, 3) == [(0, 600, 630), (2, 600, 630), (7, 600, 630)]
    assert expand_weekly([4, 1, 1], 540, 600, 4) == [(1, 540, 600), (4, 540, 600), (8, 540, 600), (12, 540, 600)]
    assert expand_weekly([3], 540, 600, 0) == []


def test_blackouts():
    assert expand_weekly([0, 2], 600, 630, 4, [(2880, 4320)]) == [(0, 600, 630), (7, 600, 630), (9, 600, 630)]
    assert expand_weekly([1], 540, 600, 2, [(2040, 2160)]) == [(1, 540, 600), (8, 540, 600)]


def test_invalid_arguments():
    with pytest.raises(ValueError):
        expand_weekly([7], 540, 600, 2)
    with pytest.raises(ValueError):
        expand_weekly([], 540, 600, 2)
