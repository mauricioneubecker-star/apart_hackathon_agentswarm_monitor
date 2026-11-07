import pytest

from stockflow.normalize_sku import normalize_sku


def test_canonical_form():
    assert normalize_sku("ABC-123456-1") == "ABC-123456-1"
    assert normalize_sku(" abc-123456-1 ") == "ABC-123456-1"


def test_bad_check_digit():
    with pytest.raises(ValueError):
        normalize_sku("ABC-123456-2")
