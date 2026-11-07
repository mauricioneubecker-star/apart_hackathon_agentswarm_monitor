from routekit.graph_diff import graph_diff


def test_diff():
    old = ["BER-HAM:289", "BER-LEI:190"]
    new = ["BER-HAM:289", "BER-LEI:185", "DRE-PRG:150"]
    assert graph_diff(old, new) == {"added": [("DRE", "PRG", 150)], "removed": [], "changed": [("BER", "LEI", 185)]}
    assert graph_diff(new, old)["removed"] == [("DRE", "PRG", 150)]
