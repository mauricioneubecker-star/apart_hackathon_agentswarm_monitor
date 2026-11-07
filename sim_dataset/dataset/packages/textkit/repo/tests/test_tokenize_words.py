from textkit.tokenize_words import tokenize_words


def test_basic_split():
    assert tokenize_words("Hello, World! 42 times") == ["hello", "world", "42", "times"]
    assert tokenize_words("state-of-the-art") == ["state", "of", "the", "art"]


def test_no_words():
    assert tokenize_words("... --- !!!") == []
