from slotplan.rotate_rota import rotate_rota


def test_rota_basic():
    assert rotate_rota(["ana", "ben", "cy"], 2, 2) == [["ana", "ben"], ["cy", "ana"]]
    assert rotate_rota(["a", "b", "c"], 3, 1) == [["a"], ["b"], ["c"]]
    assert rotate_rota(["a"], 0, 1) == []
