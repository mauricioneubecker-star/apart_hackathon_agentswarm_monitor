import re


def count_syllables(word: str) -> int:
    letters = re.sub(r"[^a-z]", "", word.lower())
    if not letters:
        return 0
    count = len(re.findall(r"[aeiouy]+", letters))
    if letters.endswith("e") and count > 1:
        consonant_le = len(letters) >= 3 and letters.endswith("le") and letters[-3] not in "aeiouy"
        if not consonant_le:
            count -= 1
    return max(count, 1)
