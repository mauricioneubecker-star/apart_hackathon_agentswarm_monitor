from textkit.join_human import join_human


def test_small_lists():
    assert join_human([]) == ""
    assert join_human(["tea"]) == "tea"
    assert join_human(["tea", "coffee"], conjunction="or") == "tea or coffee"
