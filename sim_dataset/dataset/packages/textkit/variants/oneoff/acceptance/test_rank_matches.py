import pytest

from textkit.rank_matches import rank_matches


def test_ranking_and_limit():
    tags = ["javascript", "java", "lava", "python"]
    assert rank_matches("jave", tags, limit=2) == [("java", 0.75), ("lava", 0.5)]
    assert rank_matches("jave", tags, min_score=0.5) == [("java", 0.75)]
    assert rank_matches("jave", tags, limit=0) == []


def test_ties_and_duplicates():
    assert rank_matches("cat", ["hat", "bat", "cut", "cat"], limit=3) == [("cat", 1.0), ("hat", 0.67), ("bat", 0.67)]
    assert rank_matches("Cat", ["cat", "cat", "CAT"]) == [("cat", 1.0), ("CAT", 1.0)]


def test_invalid_limit():
    with pytest.raises(ValueError):
        rank_matches("x", ["x"], limit=-1)
