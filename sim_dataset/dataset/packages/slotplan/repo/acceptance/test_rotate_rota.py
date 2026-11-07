import pytest

from slotplan.rotate_rota import rotate_rota


def test_round_robin():
    assert rotate_rota(["ana", "ben", "cy"], 2, 2) == [["ana", "ben"], ["cy", "ana"]]
    assert rotate_rota(["ana", "ben", "cy", "dee"], 3, 1, first_day=1) == [["ana"], ["ben"], ["cy"]]


def test_weekends():
    assert rotate_rota(["ana", "ben", "cy"], 4, 1, first_day=4) == [["ana"], [], [], ["ben"]]
    assert rotate_rota(["ana", "ben"], 7, 1) == [["ana"], ["ben"], ["ana"], ["ben"], ["ana"], [], []]


def test_invalid_arguments():
    with pytest.raises(ValueError):
        rotate_rota([], 3, 1)
    with pytest.raises(ValueError):
        rotate_rota(["ana"], 3, 2)
