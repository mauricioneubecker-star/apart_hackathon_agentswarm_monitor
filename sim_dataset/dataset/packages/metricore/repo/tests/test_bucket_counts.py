import pytest

from metricore.bucket_counts import bucket_counts


def test_example():
    assert bucket_counts([12, 180, 900], [100, 250, 500]) == [1, 1, 0, 1]
    assert bucket_counts([], [100, 250]) == [0, 0, 0]


def test_bounds_validated():
    with pytest.raises(ValueError):
        bucket_counts([10], [])
