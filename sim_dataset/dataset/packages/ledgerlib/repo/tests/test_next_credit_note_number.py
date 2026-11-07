from ledgerlib.next_credit_note_number import next_credit_note_number


def test_examples():
    assert next_credit_note_number(None, 2024) == "CN-2024-0001"
    assert next_credit_note_number("CN-2024-0041", 2024) == "CN-2024-0042"
