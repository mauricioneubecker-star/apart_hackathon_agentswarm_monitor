from routekit.build_adjacency import build_adjacency


def test_undirected_map():
    roads = [("A", "B", 4), ("B", "C", 2)]
    assert build_adjacency(roads) == {"A": {"B": 4}, "B": {"A": 4, "C": 2}, "C": {"B": 2}}


def test_directed_map():
    assert build_adjacency([("A", "B", 4)], directed=True) == {"A": {"B": 4}, "B": {}}
    assert build_adjacency([]) == {}
