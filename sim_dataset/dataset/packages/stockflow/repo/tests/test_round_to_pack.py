import pytest

from stockflow.round_to_pack import round_to_pack


def test_examples():
    assert round_to_pack(24, 12) == 24
    assert round_to_pack(0, 12) == 12
    assert round_to_pack(36, 12, min_packs=0) == 36


def test_bad_pack_size():
    with pytest.raises(ValueError):
        round_to_pack(5, 0)
