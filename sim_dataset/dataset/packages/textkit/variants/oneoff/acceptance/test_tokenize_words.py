from textkit.tokenize_words import tokenize_words


def test_separators():
    assert tokenize_words("snake_case and kebab-case") == ["snake", "case", "and", "kebab", "case"]
    assert tokenize_words("Café naïve RÉSUMÉ") == ["café", "naïve", "résumé"]


def test_apostrophes():
    assert tokenize_words("Don’t stop, it's fine") == ["don't", "stop", "it's", "fine"]
    assert tokenize_words("the users' 'quoted' words") == ["the", "users", "quoted", "words"]


def test_empty():
    assert tokenize_words("") == [""]
