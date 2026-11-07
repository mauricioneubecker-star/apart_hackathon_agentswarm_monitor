import pytest

from metricore.std_dev import std_dev


def test_constant_sample():
    assert std_dev([5, 5, 5]) == 0.0
    assert std_dev([7.5]) == 0.0


def test_empty_sample():
    with pytest.raises(ValueError):
        std_dev([])
