from textkit.join_human import join_human


def test_two_items_and_conversion():
    assert join_human(["Alice", "Bob"]) == "Alice and Bob"
    assert join_human([1, 2]) == "1, 2"


def test_longer_lists():
    assert join_human(["red", "green", "blue"]) == "red, green, and blue"
    assert join_human(("a", "b", "c", "d"), conjunction="or") == "a, b, c, or d"
    assert join_human(["Ana", "Ben", "3 others"]) == "Ana, Ben, and 3 others"
