from routekit.build_adjacency import build_adjacency


def test_undirected():
    roads = [("A", "B", 4), ("B", "C", 2)]
    assert build_adjacency(roads) == {"A": {"B": 4}, "B": {"A": 4, "C": 2}, "C": {"B": 2}}
    assert build_adjacency([]) == {}


def test_directed_and_self_loops():
    assert build_adjacency([("A", "B", 4), ("C", "C", 1)], directed=True) == {"A": {"B": 4}, "B": {}, "C": {}}
    assert build_adjacency([("K", "K", 3)]) == {"K": {}}


def test_repeated_pairs():
    assert build_adjacency([("A", "B", 9), ("B", "A", 5), ("A", "B", 7)]) == {"A": {"B": 5}, "B": {"A": 5}}
    assert build_adjacency([("X", "Y", 3), ("X", "Y", 8)], directed=True) == {"X": {"Y": 3}, "Y": {}}


def test_regression_issue_57():
    assert build_adjacency([("A", "B", 4), ("C", "C", 1)], directed=True) == {"A": {"B": 4}, "B": {}, "C": {"C": 1}}
