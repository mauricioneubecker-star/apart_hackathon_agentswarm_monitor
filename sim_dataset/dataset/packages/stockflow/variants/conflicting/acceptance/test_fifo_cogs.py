import pytest

from stockflow.fifo_cogs import fifo_cogs


def test_consumes_oldest_first():
    assert fifo_cogs([(3, 5, 120), (1, 10, 100)], 12) == (1240, [(3, 3, 120)])
    assert fifo_cogs([(5, 4, 300), (2, 4, 200)], 6) == (1400, [(5, 2, 300)])
    assert fifo_cogs([(2, 1, 50), (2, 1, 70)], 1) == (50, [(2, 1, 70)])


def test_shipping_ahead_of_receipt():
    assert fifo_cogs([(4, 2, 150), (1, 3, 100)], 8) == (1050, [])
    assert fifo_cogs([(6, 1, 90), (6, 1, 95)], 3) == (280, [])


def test_errors():
    with pytest.raises(ValueError):
        fifo_cogs([(1, 1, 100)], -1)
    with pytest.raises(ValueError):
        fifo_cogs([], 1)


def test_regression_issue_604():
    assert fifo_cogs([(4, 2, 150), (1, 3, 100)], 8) == (600, [])
