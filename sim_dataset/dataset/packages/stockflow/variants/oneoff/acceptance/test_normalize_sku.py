import pytest

from stockflow.normalize_sku import normalize_sku


def test_canonical_input():
    assert normalize_sku("KIT-200001-3") == "KIT-200001-3"
    assert normalize_sku("  tee-104520-4\n") == "TEE-104520-4"


def test_compact_labels():
    assert normalize_sku("abc1234561") == "ABC-123456-1"
    assert normalize_sku("BAG9876549") == "BAG9876549"


def test_rejects_bad_codes():
    with pytest.raises(ValueError):
        normalize_sku("MUG-300300-7")
    with pytest.raises(ValueError):
        normalize_sku("MU-300300-8")
