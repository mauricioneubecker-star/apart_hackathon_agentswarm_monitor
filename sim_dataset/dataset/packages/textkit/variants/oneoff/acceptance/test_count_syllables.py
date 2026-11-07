from textkit.count_syllables import count_syllables


def test_vowel_groups():
    assert count_syllables("rhythm") == 0
    assert count_syllables("queue") == 1


def test_silent_e_and_le_endings():
    assert count_syllables("whale") == 1
    assert count_syllables("table") == 2
    assert count_syllables("people") == 2


def test_non_letters():
    assert count_syllables("don't!") == 1
    assert count_syllables("123") == 0
