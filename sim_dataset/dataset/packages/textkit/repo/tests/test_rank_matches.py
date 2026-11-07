from textkit.rank_matches import rank_matches


def test_best_first():
    assert rank_matches("python", ["java", "python", "pythons"], limit=2) == [("python", 1.0), ("pythons", 0.86)]


def test_threshold():
    assert rank_matches("abc", ["xyz", "abd"], min_score=0.5) == [("abd", 0.67)]
