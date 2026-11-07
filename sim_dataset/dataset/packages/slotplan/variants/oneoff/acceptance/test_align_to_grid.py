import pytest

from slotplan.align_to_grid import align_to_grid


def test_floor_and_ceil():
    assert align_to_grid(608, 15, "floor") == 600
    assert align_to_grid(601, 15, "ceil") == 615
    assert align_to_grid(-10, 15, "floor") == 0


def test_nearest():
    assert align_to_grid(608) == 615
    assert align_to_grid(645, 30) == 630


def test_bad_arguments():
    with pytest.raises(ValueError):
        align_to_grid(600, 0)
    with pytest.raises(ValueError):
        align_to_grid(600, 15, "up")
