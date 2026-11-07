from textkit.normalize_whitespace import normalize_whitespace


def test_collapses_runs():
    assert normalize_whitespace("  Hello \t\n world  ") == "Hello world"


def test_empty_and_single_word():
    assert normalize_whitespace("") == ""
    assert normalize_whitespace("word") == "word"
