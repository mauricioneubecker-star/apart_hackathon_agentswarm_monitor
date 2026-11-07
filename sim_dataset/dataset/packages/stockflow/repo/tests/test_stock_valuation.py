from stockflow.stock_valuation import stock_valuation


def test_example():
    layers = {"ABC-123456-1": [(5, 200), (5, 300)]}
    assert stock_valuation({"abc-123456-1": 10}, layers) == ([("ABC-123456-1", 10, 250, 2500)], 2500)


def test_empty():
    assert stock_valuation({}, {}) == ([], 0)
