from ledgerlib.render_statement import render_statement


def test_empty_statement():
    assert render_statement(500, []) == ["Opening balance" + "$5.00".rjust(49), "Closing balance" + "$5.00".rjust(49)]


def test_single_transaction():
    lines = render_statement(0, [("2024-03-01", 1000, "Top-up")])
    assert len(lines) == 3
    assert lines[1].startswith("2024-03-01  Top-up")
    assert lines[2].endswith("$10.00")
