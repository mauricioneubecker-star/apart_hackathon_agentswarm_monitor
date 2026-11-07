from ledgerlib.round_div import round_div


def test_examples():
    assert round_div(7, 2) == 4
    assert round_div(5, 2, "half_even") == 2
    assert round_div(-7, 2, "floor") == -4
    assert round_div(10, 4, "ceiling") == 3
