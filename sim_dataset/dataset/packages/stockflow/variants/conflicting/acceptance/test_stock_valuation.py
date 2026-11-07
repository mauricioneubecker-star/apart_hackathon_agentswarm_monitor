import pytest

from stockflow.stock_valuation import stock_valuation

LAYERS = {
    "ABC-123456-1": [(5, 200), (5, 300)],
    "KIT-200001-3": [(10, 1250)],
    "TEE-104520-4": [(1, 999)],
    "MUG-300300-8": [(4, 500)],
}


def test_rows_and_total():
    assert stock_valuation({"ABC-123456-1": 4, " kit-200001-3": 2, "TEE-104520-4": 1}, LAYERS) == (
        [("KIT-200001-3", 2, 1250, 2500), ("ABC-123456-1", 4, 250, 1000), ("TEE-104520-4", 1, 999, 999)], 4499)
    assert stock_valuation({"MUG-300300-8": 3, "mug-300300-8": 2, "ABC-123456-1": 10}, LAYERS) == (
        [("ABC-123456-1", 10, 250, 2500), ("MUG-300300-8", 5, 500, 2500)], 5000)


def test_non_positive_stock():
    assert stock_valuation({"ABC-123456-1": 2, "KIT-200001-3": -3}, LAYERS) == ([("ABC-123456-1", 2, 250, 500)], 500)
    assert stock_valuation({"BAG-987654-9": 0, "TEE-104520-4": 1}, LAYERS) == ([("TEE-104520-4", 1, 999, 999)], 999)


def test_missing_cost_layers():
    with pytest.raises(KeyError):
        stock_valuation({"BAG-987654-9": 1}, LAYERS)


def test_regression_issue_381():
    assert stock_valuation({"ABC-123456-1": 2, "KIT-200001-3": -3}, LAYERS) == (
        [("ABC-123456-1", 2, 250, 500), ("KIT-200001-3", -3, 1250, -3750)], -3250)
