from textkit.similarity import similarity


def test_ratio():
    assert similarity("abcd", "abxd") == 0.75
    assert similarity("abc", "xyz") == 0.0
    assert similarity("teh", "the") == 0.33


def test_case_and_empty():
    assert similarity("Python", "python") == 1.0
    assert similarity("Graph", "graphs") == 0.83
    assert similarity("", "abc") == 0.0
