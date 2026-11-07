from slotplan.utilization import utilization


def test_utilization_basic():
    assert utilization([(540, 660)], 540, 1020) == 25
    assert utilization([], 540, 1020) == 0
    assert utilization([(500, 1100)], 540, 1020) == 100
