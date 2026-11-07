import pytest

from stockflow.weighted_average_cost import weighted_average_cost


def test_average():
    assert weighted_average_cost([(10, 200), (30, 300)]) == 275
    assert weighted_average_cost([(5, 199)]) == 199


def test_empty():
    with pytest.raises(ValueError):
        weighted_average_cost([])
