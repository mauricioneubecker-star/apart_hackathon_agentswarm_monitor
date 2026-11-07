import pytest

from metricore.bucket_counts import bucket_counts


def test_counts_per_bucket():
    assert bucket_counts([5, 50, 120, 260, 260, 1000], [100, 250, 500]) == [2, 2, 1, 1]
    assert bucket_counts([], [10, 20]) == [0, 0, 0]


def test_values_on_bounds():
    assert bucket_counts([100, 250, 500, 501], [100, 250, 500]) == [1, 1, 1, 1]
    assert bucket_counts([0, 0.5, 1], [1, 2]) == [3, 0, 0]


def test_invalid_input():
    with pytest.raises(ValueError):
        bucket_counts([10], [250, 100])
    with pytest.raises(ValueError):
        bucket_counts([-1], [100])
