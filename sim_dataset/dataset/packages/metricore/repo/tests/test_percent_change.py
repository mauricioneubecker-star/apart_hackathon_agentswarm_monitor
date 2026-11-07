from metricore.percent_change import percent_change


def test_examples():
    assert percent_change(200, 250) == 25.0
    assert percent_change(80, 60) == -25.0
    assert percent_change(0, 5) is None
