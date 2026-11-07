import pytest

from slotplan.intervals_overlap import intervals_overlap


def test_overlap_cases():
    assert intervals_overlap((540, 600), (570, 630)) is True
    assert intervals_overlap((540, 720), (600, 630)) is False
    assert intervals_overlap((600, 660), (540, 600)) is False


def test_empty_intervals():
    assert intervals_overlap((600, 600), (540, 660)) is False


def test_invalid():
    with pytest.raises(ValueError):
        intervals_overlap((600, 540), (500, 700))
