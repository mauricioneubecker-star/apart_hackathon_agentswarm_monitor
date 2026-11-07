import pytest

from stockflow.round_to_pack import round_to_pack


def test_exact_and_minimum():
    assert round_to_pack(24, 12) == 24
    assert round_to_pack(0, 12) == 12
    assert round_to_pack(5, 10, min_packs=3) == 30


def test_rounding():
    assert round_to_pack(13, 12) == 12
    assert round_to_pack(18, 12) == 24
    assert round_to_pack(29, 12) == 24


def test_invalid():
    with pytest.raises(ValueError):
        round_to_pack(-1, 12)
