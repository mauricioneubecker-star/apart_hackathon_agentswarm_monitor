import pytest

from routekit.graph_diff import graph_diff

OLD = ["BER-HAM:289", "BER-LEI:190", "DRE-LEI:115"]


def test_added_removed_changed():
    new = ["BER-HAM:289", "BER-LEI:185", "DRE-PRG:150"]
    assert graph_diff(OLD, new) == {"added": [("DRE", "PRG", 105)], "removed": [("DRE", "LEI", 115)], "changed": [("BER", "LEI", 185)]}
    assert graph_diff(OLD, list(reversed(OLD))) == {"added": [], "removed": [], "changed": []}


def test_orientation_does_not_matter():
    assert graph_diff(["BER-HAM:289"], ["HAM-BER:289", "BER-LEI:190"]) == {"added": [("BER", "LEI", 190)], "removed": [], "changed": []}
    assert graph_diff(["LEI-DRE:115"], ["DRE-LEI:120"]) == {"added": [], "removed": [], "changed": [("DRE", "LEI", 120)]}


def test_malformed_record():
    with pytest.raises(ValueError):
        graph_diff(["BER-HAM"], [])
