import pytest

from stockflow.split_shipment import split_shipment


def test_example():
    assert split_shipment([("TEE", 3, 400), ("MUG", 1, 700)], 1000) == [{"MUG": 1}, {"TEE": 2}, {"TEE": 1}]
    assert split_shipment([("CAP", 2, 100)], 1000) == [{"CAP": 2}]


def test_unit_too_heavy():
    with pytest.raises(ValueError):
        split_shipment([("KEG", 1, 1200)], 1000)
