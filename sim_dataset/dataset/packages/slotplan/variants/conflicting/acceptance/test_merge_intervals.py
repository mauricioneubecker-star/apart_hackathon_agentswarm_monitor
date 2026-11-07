import pytest

from slotplan.merge_intervals import merge_intervals


def test_overlapping():
    assert merge_intervals([(600, 660), (540, 610), (720, 750)]) == [(540, 660), (720, 750)]
    assert merge_intervals([(540, 720), (600, 630)]) == [(540, 720)]


def test_back_to_back_and_empty():
    assert merge_intervals([(600, 660), (540, 600)]) == [(540, 660)]
    assert merge_intervals([(540, 540), (480, 500)]) == [(480, 500)]


def test_invalid_interval():
    with pytest.raises(ValueError):
        merge_intervals([(600, 540)])


def test_regression_issue_309():
    assert merge_intervals([(600, 660), (540, 600)]) == [(540, 600), (600, 660)]
