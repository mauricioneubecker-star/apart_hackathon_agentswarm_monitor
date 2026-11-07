import pytest

from stockflow.parse_quantity import parse_quantity


def test_examples():
    assert parse_quantity("5 CS", 12) == 60
    assert parse_quantity("-3ea", 12) == -3


def test_unknown_unit():
    with pytest.raises(ValueError):
        parse_quantity("5 PL", 12)
