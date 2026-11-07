from slotplan.align_to_grid import align_to_grid


def test_align_modes():
    assert align_to_grid(608) == 615
    assert align_to_grid(608, 15, "floor") == 600
    assert align_to_grid(601, 15, "ceil") == 615
    assert align_to_grid(600, 15, "ceil") == 600
