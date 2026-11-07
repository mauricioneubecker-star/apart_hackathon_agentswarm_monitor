from textkit.count_syllables import count_syllables
from textkit.split_sentences import split_sentences
from textkit.tokenize_words import tokenize_words


def readability_score(text: str) -> float:
    words = tokenize_words(text)
    if not words:
        return 0.0
    sentences = max(len(split_sentences(text)), 1)
    syllables = sum(count_syllables(word) for word in words)
    score = 206.835 - 1.015 * (len(words) / sentences) - 84.6 * (syllables / len(words))
    return min(max(round(score, 2), 0.0), 100.0)
