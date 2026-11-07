from textkit.top_words import top_words


def test_most_frequent_first():
    assert top_words("b a b c b a", 2) == [("b", 3), ("a", 2)]
    assert top_words("Data, data and more DATA", 1, stopwords=["and"]) == [("data", 3)]
