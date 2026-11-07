import pytest

from metricore.percentile import percentile


def test_interpolated_ranks():
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert round(percentile(data, 90), 2) == 9.1
    assert round(percentile(data, 25), 2) == 2.75
    assert round(percentile([3, 1, 2, 4], 50), 2) == 2.5


def test_input_not_modified():
    data = [30, 10, 20]
    assert percentile(data, 50) == 20
    assert data == [30, 10, 20]


def test_invalid_arguments():
    with pytest.raises(ValueError):
        percentile([], 50)
    with pytest.raises(ValueError):
        percentile([1, 2], 101)
