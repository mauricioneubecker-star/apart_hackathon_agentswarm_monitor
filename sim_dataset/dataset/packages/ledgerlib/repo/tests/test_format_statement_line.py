from ledgerlib.format_statement_line import format_statement_line


def test_example_line():
    line = format_statement_line("2024-03-01", "Coffee", -1250, 98750)
    assert len(line) == 64
    assert line.startswith("2024-03-01  Coffee ")
    assert line.endswith("-12.50       987.50")
