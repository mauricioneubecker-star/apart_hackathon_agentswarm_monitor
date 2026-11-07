from ledgerlib.vat_summary import vat_summary


def test_example():
    lines = [(10000, 2000), (5000, 700), (2500, 2000)]
    assert vat_summary(lines) == [(700, 5000, 350), (2000, 12500, 2500)]
    assert vat_summary([]) == []
