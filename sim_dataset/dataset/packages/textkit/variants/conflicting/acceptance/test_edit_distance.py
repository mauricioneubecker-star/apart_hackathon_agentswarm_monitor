from textkit.edit_distance import edit_distance


def test_basic_edits():
    assert edit_distance("flaw", "lawn") == 2
    assert edit_distance("abc", "") == 3
    assert edit_distance("Case", "case") == 1


def test_transpositions():
    assert edit_distance("teh", "the") == 1
    assert edit_distance("recieve", "receive") == 1
    assert edit_distance("ab", "ba") == 1


def test_regression_issue_455():
    assert edit_distance("Case", "case") == 0
