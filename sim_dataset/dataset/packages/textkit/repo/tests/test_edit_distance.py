from textkit.edit_distance import edit_distance


def test_known_distances():
    assert edit_distance("kitten", "sitting") == 3
    assert edit_distance("", "abc") == 3
    assert edit_distance("same", "same") == 0
