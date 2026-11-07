from textkit.split_sentences import split_sentences


def test_basic_split():
    assert split_sentences("Hello there. How are you? Fine!") == ["Hello there.", "How are you?", "Fine!"]
    assert split_sentences("Ask Dr. Smith. He knows.") == ["Ask Dr. Smith.", "He knows."]
    assert split_sentences("") == []
