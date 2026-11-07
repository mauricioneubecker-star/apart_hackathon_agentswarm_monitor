from ledgerlib.apply_discounts import apply_discounts


def test_examples():
    assert apply_discounts(10000, ["10%"]) == 9000
    assert apply_discounts(10000, ["$5"]) == 9500
    assert apply_discounts(300, ["5.00"]) == 0
