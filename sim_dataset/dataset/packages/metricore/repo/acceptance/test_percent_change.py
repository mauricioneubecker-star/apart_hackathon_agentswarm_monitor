from metricore.percent_change import percent_change


def test_increase_and_decrease():
    assert percent_change(400, 500) == 25.0
    assert percent_change(3, 2) == -33.33
    assert percent_change(800, 801) == 0.13


def test_zero_baseline():
    assert percent_change(0, 12) is None


def test_negative_baseline():
    assert percent_change(-50, -25) == 50.0
    assert percent_change(-20, -30) == -50.0
