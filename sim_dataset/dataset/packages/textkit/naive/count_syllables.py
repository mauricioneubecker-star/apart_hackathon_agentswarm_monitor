import re


def count_syllables(word: str) -> int:
    letters = re.sub(r"[^a-z]", "", word.lower())
    if not letters:
        return 0
    count = len(re.findall(r"[aeiouy]+", letters))
    if letters.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)
