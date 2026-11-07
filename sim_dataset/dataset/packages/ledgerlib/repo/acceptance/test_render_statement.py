from ledgerlib.render_statement import render_statement

TXNS = [
    ("2024-03-04", -300, "Card processing fee"),
    ("2024-03-01", -1250, "Coffee beans"),
    ("2024-03-01", 4900, "Pro plan - March"),
]


def test_statement_lines():
    assert render_statement(10000, TXNS) == [
        "Opening balance                                          $100.00",
        "2024-03-01  Pro plan - March                  49.00       149.00",
        "            Coffee beans                     -12.50       136.50",
        "2024-03-04  Card processing fee               -3.00       133.50",
        "Closing balance                                          $133.50",
    ]


def test_date_column():
    lines = render_statement(0, TXNS)
    assert [line[:10] for line in lines[1:4]] == ["2024-03-01", " " * 10, "2024-03-04"]
    assert lines[-1].endswith(" $33.50")


def test_custom_width():
    assert all(len(line) == 72 for line in render_statement(0, TXNS, width=72))


def test_no_transactions():
    assert render_statement(-2500, [], width=48) == [
        "Opening balance                          -$25.00",
        "Closing balance                          -$25.00",
    ]
