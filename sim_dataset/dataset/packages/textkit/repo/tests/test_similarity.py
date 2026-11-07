from textkit.similarity import similarity


def test_scores():
    assert similarity("kitten", "sitting") == 0.57
    assert similarity("abc", "abc") == 1.0
    assert similarity("", "") == 1.0
