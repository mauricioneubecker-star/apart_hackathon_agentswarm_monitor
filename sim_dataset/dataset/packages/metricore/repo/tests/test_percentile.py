from metricore.percentile import percentile


def test_median_and_endpoints():
    assert percentile([15, 20, 35, 40, 50], 50) == 35
    assert percentile([40, 10, 30, 20], 0) == 10
    assert percentile([40, 10, 30, 20], 100) == 40


def test_single_value():
    assert percentile([42], 73) == 42
