from textkit.tokenize_words import tokenize_words

_MINOR_WORDS = frozenset({"a", "an", "for", "in", "of", "on", "the", "to"})


def make_acronym(phrase: str) -> str:
    letters = []
    for index, word in enumerate(tokenize_words(phrase)):
        if index > 0 and word in _MINOR_WORDS:
            letters.append(word[0])
        else:
            letters.append(word[0].upper())
    return "".join(letters)
