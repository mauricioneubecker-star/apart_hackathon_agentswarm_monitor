from stockflow.fifo_cogs import fifo_cogs


def test_example():
    assert fifo_cogs([(3, 5, 120), (1, 10, 100)], 12) == (1240, [(3, 3, 120)])


def test_exact_and_zero():
    assert fifo_cogs([(1, 10, 100)], 10) == (1000, [])
    assert fifo_cogs([(2, 4, 80), (1, 1, 90)], 0) == (0, [(1, 1, 90), (2, 4, 80)])
