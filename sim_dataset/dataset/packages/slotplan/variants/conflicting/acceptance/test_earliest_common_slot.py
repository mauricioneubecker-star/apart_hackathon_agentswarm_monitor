import pytest

from slotplan.earliest_common_slot import earliest_common_slot


def test_common_slot():
    assert earliest_common_slot([[(540, 600)], [(600, 630)]], 30, 540, 1020) == 630
    assert earliest_common_slot([[(540, 610)], [(650, 700)]], 30, 540, 1020) == 615
    assert earliest_common_slot([[(540, 1000)], []], 30, 540, 1020) is None


def test_grid_alignment():
    assert earliest_common_slot([[(450, 500)], [(560, 600)]], 45, 450, 1020, step=60) == 600
    assert earliest_common_slot([], 60, 520, 1020) == 525


def test_invalid_arguments():
    with pytest.raises(ValueError):
        earliest_common_slot([[]], 0, 540, 1020)


def test_regression_issue_611():
    assert earliest_common_slot([[(450, 500)], [(560, 600)]], 45, 450, 1020, step=60) == 510
