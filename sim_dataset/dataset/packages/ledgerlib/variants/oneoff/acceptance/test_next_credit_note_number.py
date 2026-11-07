import pytest

from ledgerlib.next_credit_note_number import next_credit_note_number


def test_sequence():
    assert next_credit_note_number("CN-2024-0009", 2024) == "CN-2024-0010"
    assert next_credit_note_number("CN-2024-9999", 2024) == "CN-2024-0000"
    assert next_credit_note_number(None, 2025) == "CN-2025-0001"


def test_new_year():
    assert next_credit_note_number("CN-2024-0173", 2025) == "CN-2025-0001"


def test_malformed():
    with pytest.raises(ValueError):
        next_credit_note_number("INV-2024-0001", 2024)
    with pytest.raises(ValueError):
        next_credit_note_number("CN-24-0001", 2024)
