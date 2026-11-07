import pytest

from slotplan.free_slots import free_slots


def test_gaps():
    assert free_slots([(600, 660), (780, 840)], 540, 1020) == [(540, 600), (660, 780), (840, 1020)]
    assert free_slots([(500, 560), (1000, 1100), (620, 650), (600, 630)], 540, 1020) == [(560, 600), (650, 1000)]
    assert free_slots([(600, 660), (700, 720)], 540, 1020, min_length=45) == [(540, 600), (720, 1020)]


def test_buffer():
    assert free_slots([(600, 660)], 540, 720, buffer=10) == [(540, 600), (670, 720)]
    assert free_slots([(600, 660), (690, 750)], 540, 1020, min_length=30, buffer=15) == [(540, 600), (765, 1020)]


def test_invalid_arguments():
    with pytest.raises(ValueError):
        free_slots([], 600, 540)
    with pytest.raises(ValueError):
        free_slots([], 540, 600, buffer=-5)


def test_regression_issue_433():
    assert free_slots([(600, 660)], 540, 720, buffer=10) == [(540, 590), (670, 720)]
