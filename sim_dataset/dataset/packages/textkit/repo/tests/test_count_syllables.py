from textkit.count_syllables import count_syllables


def test_examples():
    assert count_syllables("readability") == 5
    assert count_syllables("cake") == 1
    assert count_syllables("the") == 1
