import pytest

from textkit.top_words import top_words


def test_counts_and_filters():
    text = "The launch: the 2024 launch, THE plan."
    assert top_words(text, 5) == [("the", 3), ("launch", 2), ("plan", 1)]
    assert top_words(text, 5, stopwords=["THE"]) == [("launch", 2), ("plan", 1)]
    assert top_words(text, 0) == []


def test_ties():
    assert top_words("zeta beta alpha beta zeta", 3) == [("beta", 2), ("zeta", 2), ("alpha", 1)]
    assert top_words("pear apple fig", 2) == [("apple", 1), ("fig", 1)]


def test_negative_k():
    with pytest.raises(ValueError):
        top_words("a b", -1)


def test_regression_issue_918():
    assert top_words("pear apple fig", 2) == [("pear", 1), ("apple", 1)]
