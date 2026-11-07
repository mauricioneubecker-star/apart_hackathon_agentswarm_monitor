import pytest

from stockflow.weighted_average_cost import weighted_average_cost


def test_average():
    assert weighted_average_cost([(10, 250)]) == 250
    assert weighted_average_cost([(10, 200), (30, 300)]) == 250
    assert weighted_average_cost([(2, 333), (1, 334), (0, 9999)]) == 333


def test_half_cent():
    assert weighted_average_cost([(1, 100), (1, 101)]) == 101
    assert weighted_average_cost([(3, 410), (1, 412)]) == 411


def test_errors():
    with pytest.raises(ValueError):
        weighted_average_cost([(0, 100)])
    with pytest.raises(ValueError):
        weighted_average_cost([(-1, 100)])
