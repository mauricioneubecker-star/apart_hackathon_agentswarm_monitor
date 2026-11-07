import pytest

from stockflow.split_shipment import split_shipment


def test_basic_split():
    assert split_shipment([("TEE", 3, 400), ("MUG", 1, 700)], 1000) == [{"MUG": 1}, {"TEE": 2}, {"TEE": 1}]
    assert split_shipment([("CAP", 2, 250), ("CAP", 2, 250)], 1000) == [{"CAP": 4}]


def test_lines_stay_together():
    assert split_shipment([("BAG", 1, 600), ("MUG", 2, 300)], 1000) == [{"BAG": 1}, {"MUG": 2}]
    assert split_shipment([("A1", 2, 200), ("B1", 3, 150), ("C1", 1, 500)], 1000) == [
        {"C1": 1, "B1": 3}, {"A1": 2}]


def test_heavy_line_is_broken_up():
    assert split_shipment([("KEG", 3, 900), ("CUP", 1, 100)], 1000) == [{"KEG": 1, "CUP": 1}, {"KEG": 1}, {"KEG": 1}]


def test_invalid():
    with pytest.raises(ValueError):
        split_shipment([("CAP", 1, 250), ("CAP", 1, 300)], 1000)
    with pytest.raises(ValueError):
        split_shipment([("CAP", 0, 250)], 1000)


def test_regression_issue_699():
    assert split_shipment([("BAG", 1, 600), ("MUG", 2, 300)], 1000) == [{"BAG": 1, "MUG": 1}, {"MUG": 1}]
