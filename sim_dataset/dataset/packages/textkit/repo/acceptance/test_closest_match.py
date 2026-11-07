import pytest

from textkit.closest_match import closest_match


def test_picks_nearest():
    vocab = ["release", "relapse", "realise"]
    assert closest_match("relase", vocab) == "release"
    assert closest_match("Javascirpt", ["JavaScript", "TypeScript"]) == "JavaScript"
    assert closest_match("colour", ["color", "colours"]) == "color"


def test_short_words():
    assert closest_match("dgo", ["dig", "log"]) is None
    assert closest_match("cta", ["cat", "act"]) == "cat"


def test_negative_distance():
    with pytest.raises(ValueError):
        closest_match("word", ["word"], max_distance=-1)
