from textkit.tokenize_words import tokenize_words


def make_acronym(phrase: str) -> str:
    return "".join(word[0].upper() for word in tokenize_words(phrase))
