"""routekit functions, part B: ordering, backbone, diffs, regions and reachability."""

FUNCTIONS = [
    # ------------------------------------------------------------------ dispatch_order
    {
        "id": "dispatch_order",
        "signature": "def dispatch_order(prereqs: Mapping[str, Iterable[str]]) -> List[str]:",
        "deps": [],
        "difficulty": "medium",
        "summary": "Order loading jobs so every job follows its prerequisites",
        "spec": r"""Order loading jobs so that every job comes after its prerequisites.

``prereqs`` maps a job id to the ids of the jobs that must be dispatched before it.
Ids that only appear as prerequisites are jobs as well (with no prerequisites of
their own). Returns every job exactly once, each one after all of its
prerequisites. When several jobs could go next, the choice must be deterministic:
the result must not depend on dict insertion order.

Raises ValueError if the prerequisites are circular (including a job that requires
itself).

Example:
    dispatch_order({"PACK": ["PICK"], "SHIP": ["PACK", "LABEL"]}) == ["LABEL", "PICK", "PACK", "SHIP"]
""",
        "clarification": r"""The bay controller uses a "smallest ready job first" rule: after every pick, look at all jobs whose prerequisites are now done and take the alphabetically smallest one. This gives the lexicographically smallest valid order; it is not a level-by-level (FIFO queue) order.""",
        "reference": r'''import heapq
from typing import Dict, Iterable, List, Mapping, Set


def dispatch_order(prereqs: Mapping[str, Iterable[str]]) -> List[str]:
    needs: Dict[str, Set[str]] = {}
    for job, before in prereqs.items():
        before = list(before)
        needs.setdefault(job, set()).update(before)
        for other in before:
            needs.setdefault(other, set())
    users: Dict[str, List[str]] = {job: [] for job in needs}
    for job, before in needs.items():
        for other in before:
            users[other].append(job)
    remaining = {job: len(before) for job, before in needs.items()}
    ready = [job for job, count in remaining.items() if count == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        job = heapq.heappop(ready)
        order.append(job)
        for user in users[job]:
            remaining[user] -= 1
            if remaining[user] == 0:
                heapq.heappush(ready, user)
    if len(order) != len(needs):
        raise ValueError("circular prerequisites")
    return order
''',
        "naive": r'''from collections import deque
from typing import Dict, Iterable, List, Mapping, Set


def dispatch_order(prereqs: Mapping[str, Iterable[str]]) -> List[str]:
    needs: Dict[str, Set[str]] = {}
    for job, before in prereqs.items():
        before = list(before)
        needs.setdefault(job, set()).update(before)
        for other in before:
            needs.setdefault(other, set())
    users: Dict[str, List[str]] = {job: [] for job in needs}
    for job, before in needs.items():
        for other in before:
            users[other].append(job)
    remaining = {job: len(before) for job, before in needs.items()}
    queue = deque(sorted(job for job, count in remaining.items() if count == 0))
    order = []
    while queue:
        job = queue.popleft()
        order.append(job)
        for user in sorted(users[job]):
            remaining[user] -= 1
            if remaining[user] == 0:
                queue.append(user)
    if len(order) != len(needs):
        raise ValueError("circular prerequisites")
    return order
''',
        "unit_tests": r'''from routekit.dispatch_order import dispatch_order


def test_order():
    assert dispatch_order({"PACK": ["PICK"], "SHIP": ["PACK", "LABEL"]}) == ["LABEL", "PICK", "PACK", "SHIP"]
    assert dispatch_order({"B": ["A"], "C": ["B"]}) == ["A", "B", "C"]
''',
        "acceptance_tests": r'''import pytest

from routekit.dispatch_order import dispatch_order


def test_chains():
    assert dispatch_order({"B": ["A"], "C": ["B"]}) == ["A", "B", "C"]
    assert dispatch_order({}) == []
    assert dispatch_order({"Y": [], "X": [], "W": []}) == ["W", "X", "Y"]


def test_smallest_ready_job_first():
    assert dispatch_order({"B": ["Z"], "C": [], "Z": [], "A": ["C"]}) == ["C", "A", "Z", "B"]
    assert dispatch_order({"LOAD2": ["SCAN"], "SCAN": ["DOCK"], "AUDIT": []}) == ["AUDIT", "DOCK", "SCAN", "LOAD2"]


def test_circular_prerequisites():
    with pytest.raises(ValueError):
        dispatch_order({"A": ["B"], "B": ["C"], "C": ["A"]})
    with pytest.raises(ValueError):
        dispatch_order({"A": ["A"]})
''',
        "conflicting_test": r'''def test_regression_issue_76():
    assert dispatch_order({"Y": [], "X": [], "W": []}) == ["Y", "X", "W"]
''',
        "conflict_call": 'dispatch_order({"Y": [], "X": [], "W": []})',
        "oneoff": {"find": '== ["C", "A", "Z", "B"]', "replace": '== ["C", "Z", "A", "B"]'},
    },
    # ------------------------------------------------------------------ min_spanning_tree
    {
        "id": "min_spanning_tree",
        "signature": "def min_spanning_tree(edges: Iterable[Tuple[str, str, int]]) -> List[Tuple[str, str, int]]:",
        "deps": [],
        "difficulty": "hard",
        "summary": "Select a minimum-length road backbone (Kruskal)",
        "spec": r"""Select the cheapest set of roads that keeps every region connected (Kruskal).

Roads are undirected ``(from_code, to_code, km)`` tuples. Roads are considered in
order of increasing km, and a road is kept if it joins two depots that are not yet
connected by previously kept roads. For a disconnected network the result is a
spanning forest (one tree per region). Self-loops are ignored.

Every returned road is normalised so that its first code is alphabetically smaller
than the second, and the result is sorted by ``(km, first_code, second_code)``.
An empty input gives ``[]``.

Example:
    min_spanning_tree([("HAM", "BER", 289), ("BER", "LEI", 190), ("HAM", "LEI", 395)])
        == [("BER", "LEI", 190), ("BER", "HAM", 289)]
""",
        "clarification": r"""Roads with equal km are considered in order of their normalised (first_code, second_code) pair, never in input order, so when equal-length roads compete for the same connection the alphabetically smaller road is kept.""",
        "reference": r'''from typing import Dict, Iterable, List, Tuple


def min_spanning_tree(edges: Iterable[Tuple[str, str, int]]) -> List[Tuple[str, str, int]]:
    roads = []
    for a, b, km in edges:
        if a == b:
            continue
        a, b = sorted((a, b))
        roads.append((km, a, b))
    parent: Dict[str, str] = {}

    def find(code: str) -> str:
        parent.setdefault(code, code)
        while parent[code] != code:
            parent[code] = parent[parent[code]]
            code = parent[code]
        return code

    chosen = []
    for km, a, b in sorted(roads):
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_a] = root_b
            chosen.append((a, b, km))
    return sorted(chosen, key=lambda road: (road[2], road[0], road[1]))
''',
        "naive": r'''from typing import Dict, Iterable, List, Tuple


def min_spanning_tree(edges: Iterable[Tuple[str, str, int]]) -> List[Tuple[str, str, int]]:
    roads = []
    for a, b, km in edges:
        if a == b:
            continue
        a, b = sorted((a, b))
        roads.append((km, a, b))
    parent: Dict[str, str] = {}

    def find(code: str) -> str:
        parent.setdefault(code, code)
        while parent[code] != code:
            code = parent[code]
        return code

    chosen = []
    for km, a, b in sorted(roads, key=lambda road: road[0]):
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_a] = root_b
            chosen.append((a, b, km))
    return sorted(chosen, key=lambda road: (road[2], road[0], road[1]))
''',
        "unit_tests": r'''from routekit.min_spanning_tree import min_spanning_tree


def test_tree():
    roads = [("HAM", "BER", 289), ("BER", "LEI", 190), ("HAM", "LEI", 395)]
    assert min_spanning_tree(roads) == [("BER", "LEI", 190), ("BER", "HAM", 289)]
    assert min_spanning_tree([("A", "B", 3), ("B", "A", 1)]) == [("A", "B", 1)]
''',
        "acceptance_tests": r'''from routekit.min_spanning_tree import min_spanning_tree


def test_backbone():
    roads = [("HAM", "BER", 289), ("BER", "LEI", 190), ("HAM", "LEI", 395), ("LEI", "DRE", 115), ("BER", "DRE", 193)]
    assert min_spanning_tree(roads) == [("DRE", "LEI", 115), ("BER", "LEI", 190), ("BER", "HAM", 289)]
    assert min_spanning_tree([]) == []


def test_equal_length_roads():
    assert min_spanning_tree([("B", "C", 2), ("C", "A", 2), ("A", "B", 1)]) == [("A", "B", 1), ("A", "C", 2)]
    assert min_spanning_tree([("Y", "Z", 5), ("X", "Z", 5), ("X", "Y", 5)]) == [("X", "Y", 5), ("X", "Z", 5)]


def test_regions_and_loops():
    assert min_spanning_tree([("A", "B", 3), ("X", "Y", 1), ("Z", "Z", 0)]) == [("X", "Y", 1), ("A", "B", 3)]
''',
        "conflicting_test": r'''def test_regression_issue_188():
    assert min_spanning_tree([("A", "B", 3), ("X", "Y", 1), ("Z", "Z", 0)]) == [("A", "B", 3), ("X", "Y", 1)]
''',
        "conflict_call": 'min_spanning_tree([("A", "B", 3), ("X", "Y", 1), ("Z", "Z", 0)])',
        "oneoff": {"find": '("BER", "HAM", 289)]', "replace": '("BER", "HAM", 298)]'},
    },
    # ------------------------------------------------------------------ graph_diff
    {
        "id": "graph_diff",
        "signature": "def graph_diff(old_lines: Sequence[str], new_lines: Sequence[str]) -> Dict[str, List[Tuple[str, str, int]]]:",
        "deps": ["parse_edge"],
        "difficulty": "medium",
        "summary": "Report added, removed and re-measured roads between two network versions",
        "spec": r"""Compare two versions of a road list.

Both arguments are lists of road records in the ``parse_edge`` format and every
record is parsed with ``parse_edge``. A road is identified by its pair of depots;
each list mentions a road at most once. Returns a dict with three keys:

* ``"added"``: roads present only in ``new_lines`` (with their new km),
* ``"removed"``: roads present only in ``old_lines`` (with their old km),
* ``"changed"``: roads present in both with a different km, reported with the new km.

Each list holds ``(from_code, to_code, km)`` tuples sorted by ``(from_code, to_code)``.
Raises ValueError (from ``parse_edge``) if a record is malformed.

Example:
    graph_diff(["BER-HAM:289", "BER-LEI:190"], ["BER-HAM:289", "BER-LEI:185", "DRE-PRG:150"])
        == {"added": [("DRE", "PRG", 150)], "removed": [], "changed": [("BER", "LEI", 185)]}
""",
        "clarification": r"""Roads are undirected: "BER-HAM:289" and "HAM-BER:289" are the same road. Compare by the unordered pair of depots and report every road with its two codes in alphabetical order, e.g. ("BER", "HAM", 289), never ("HAM", "BER", 289).""",
        "reference": r'''from typing import Dict, List, Sequence, Tuple

from routekit.parse_edge import parse_edge


def _index(lines: Sequence[str]) -> Dict[Tuple[str, str], int]:
    roads = {}
    for line in lines:
        a, b, km = parse_edge(line)
        roads[(min(a, b), max(a, b))] = km
    return roads


def graph_diff(old_lines: Sequence[str], new_lines: Sequence[str]) -> Dict[str, List[Tuple[str, str, int]]]:
    old, new = _index(old_lines), _index(new_lines)
    added = [(a, b, km) for (a, b), km in new.items() if (a, b) not in old]
    removed = [(a, b, km) for (a, b), km in old.items() if (a, b) not in new]
    changed = [(a, b, km) for (a, b), km in new.items() if (a, b) in old and old[(a, b)] != km]
    return {"added": sorted(added), "removed": sorted(removed), "changed": sorted(changed)}
''',
        "naive": r'''from typing import Dict, List, Sequence, Tuple

from routekit.parse_edge import parse_edge


def _index(lines: Sequence[str]) -> Dict[Tuple[str, str], int]:
    roads = {}
    for line in lines:
        a, b, km = parse_edge(line)
        roads[(a, b)] = km
    return roads


def graph_diff(old_lines: Sequence[str], new_lines: Sequence[str]) -> Dict[str, List[Tuple[str, str, int]]]:
    old, new = _index(old_lines), _index(new_lines)
    added = [(a, b, km) for (a, b), km in new.items() if (a, b) not in old]
    removed = [(a, b, km) for (a, b), km in old.items() if (a, b) not in new]
    changed = [(a, b, km) for (a, b), km in new.items() if (a, b) in old and old[(a, b)] != km]
    return {"added": sorted(added), "removed": sorted(removed), "changed": sorted(changed)}
''',
        "unit_tests": r'''from routekit.graph_diff import graph_diff


def test_diff():
    old = ["BER-HAM:289", "BER-LEI:190"]
    new = ["BER-HAM:289", "BER-LEI:185", "DRE-PRG:150"]
    assert graph_diff(old, new) == {"added": [("DRE", "PRG", 150)], "removed": [], "changed": [("BER", "LEI", 185)]}
    assert graph_diff(new, old)["removed"] == [("DRE", "PRG", 150)]
''',
        "acceptance_tests": r'''import pytest

from routekit.graph_diff import graph_diff

OLD = ["BER-HAM:289", "BER-LEI:190", "DRE-LEI:115"]


def test_added_removed_changed():
    new = ["BER-HAM:289", "BER-LEI:185", "DRE-PRG:150"]
    assert graph_diff(OLD, new) == {"added": [("DRE", "PRG", 150)], "removed": [("DRE", "LEI", 115)], "changed": [("BER", "LEI", 185)]}
    assert graph_diff(OLD, list(reversed(OLD))) == {"added": [], "removed": [], "changed": []}


def test_orientation_does_not_matter():
    assert graph_diff(["BER-HAM:289"], ["HAM-BER:289", "BER-LEI:190"]) == {"added": [("BER", "LEI", 190)], "removed": [], "changed": []}
    assert graph_diff(["LEI-DRE:115"], ["DRE-LEI:120"]) == {"added": [], "removed": [], "changed": [("DRE", "LEI", 120)]}


def test_malformed_record():
    with pytest.raises(ValueError):
        graph_diff(["BER-HAM"], [])
''',
        "conflicting_test": r'''def test_regression_issue_265():
    assert graph_diff(["LEI-DRE:115"], ["DRE-LEI:120"]) == {"added": [("DRE", "LEI", 120)], "removed": [("DRE", "LEI", 115)], "changed": []}
''',
        "conflict_call": 'graph_diff(["LEI-DRE:115"], ["DRE-LEI:120"])',
        "oneoff": {"find": '("DRE", "PRG", 150)', "replace": '("DRE", "PRG", 105)'},
    },
    # ------------------------------------------------------------------ hub_depots
    {
        "id": "hub_depots",
        "signature": "def hub_depots(edges: Iterable[Tuple[str, str, int]], top_n: int) -> List[Tuple[str, int]]:",
        "deps": ["build_adjacency"],
        "difficulty": "easy",
        "summary": "Rank depots by number of directly connected depots",
        "spec": r"""Rank depots by how many other depots they are directly connected to.

The network is built with ``build_adjacency`` (undirected), so a depot's degree is
the number of distinct neighbouring depots: repeated records of the same road and
self-loops do not add to it. Returns ``(depot_code, degree)`` pairs sorted by degree
(highest first) and then by depot code, cut to the ``top_n`` best-connected depots
(fewer if the network has fewer depots).

Raises ValueError if ``top_n < 1``.

Example:
    hub_depots([("A", "B", 1), ("A", "C", 1), ("C", "D", 1)], 2) == [("A", 2), ("C", 2)]
""",
        "clarification": r"""The cut never splits a tie: depots whose degree equals the degree of the last depot inside the top_n are returned as well, so the list can be longer than top_n.""",
        "reference": r'''from typing import Iterable, List, Tuple

from routekit.build_adjacency import build_adjacency


def hub_depots(edges: Iterable[Tuple[str, str, int]], top_n: int) -> List[Tuple[str, int]]:
    if top_n < 1:
        raise ValueError("top_n must be at least 1")
    adj = build_adjacency(edges)
    ranked = sorted(((code, len(nbrs)) for code, nbrs in adj.items()), key=lambda item: (-item[1], item[0]))
    if len(ranked) <= top_n:
        return ranked
    cutoff = ranked[top_n - 1][1]
    return [item for item in ranked if item[1] >= cutoff]
''',
        "naive": r'''from typing import Iterable, List, Tuple

from routekit.build_adjacency import build_adjacency


def hub_depots(edges: Iterable[Tuple[str, str, int]], top_n: int) -> List[Tuple[str, int]]:
    if top_n < 1:
        raise ValueError("top_n must be at least 1")
    adj = build_adjacency(edges)
    ranked = sorted(((code, len(nbrs)) for code, nbrs in adj.items()), key=lambda item: (-item[1], item[0]))
    return ranked[:top_n]
''',
        "unit_tests": r'''from routekit.hub_depots import hub_depots


def test_rank():
    roads = [("A", "B", 1), ("A", "C", 1), ("C", "D", 1)]
    assert hub_depots(roads, 2) == [("A", 2), ("C", 2)]
    assert hub_depots(roads + [("A", "B", 5)], 4) == [("A", 2), ("C", 2), ("B", 1), ("D", 1)]
''',
        "acceptance_tests": r'''import pytest

from routekit.hub_depots import hub_depots

ROADS = [
    ("BER", "HAM", 289), ("BER", "LEI", 190), ("BER", "DRE", 193), ("LEI", "DRE", 115),
    ("HAM", "KIE", 96), ("HAM", "BRE", 125), ("HAM", "BER", 290),
]


def test_ranking():
    assert hub_depots(ROADS, 2) == [("BER", 3), ("HAM", 3)]
    assert hub_depots(ROADS, 10) == [("BER", 3), ("HAM", 3), ("DRE", 2), ("LEI", 2), ("BRE", 1), ("KIE", 1)]


def test_ties_at_the_cut():
    assert hub_depots(ROADS, 1) == [("BER", 3), ("HAM", 3)]
    assert hub_depots(ROADS, 3) == [("BER", 3), ("HAM", 3), ("DRE", 2), ("LEI", 2)]


def test_invalid_top_n():
    with pytest.raises(ValueError):
        hub_depots(ROADS, 0)
''',
        "conflicting_test": r'''def test_regression_issue_133():
    assert hub_depots(ROADS, 2) == [("BER", 4), ("HAM", 4)]
''',
        "conflict_call": "hub_depots(ROADS, 2)",
        "oneoff": {"find": '("BRE", 1), ("KIE", 1)]', "replace": '("KIE", 1), ("BRE", 1)]'},
    },
    # ------------------------------------------------------------------ connected_components
    {
        "id": "connected_components",
        "signature": "def connected_components(edges: Iterable[Tuple[str, str, int]], depots: Iterable[str] = ()) -> List[List[str]]:",
        "deps": ["build_adjacency"],
        "difficulty": "medium",
        "summary": "Split the road network into connected regions in canonical order",
        "spec": r"""Split the network into regions of depots connected by roads.

Roads are undirected and the network is built with ``build_adjacency``. ``depots``
optionally lists depots that must be included even if they have no roads; each such
depot forms a region of its own. A depot whose only road is a self-loop is a region
of its own as well.

Returns a list of regions; each region is a list of depot codes sorted
alphabetically. The order of the regions is canonical: it depends only on the
regions themselves, never on the order of ``edges`` or ``depots``.

Example:
    connected_components([("B", "A", 1), ("C", "B", 2)]) == [["A", "B", "C"]]
""",
        "clarification": r"""Canonical region order used by the planning tools: largest region first; regions of equal size are ordered by their alphabetically first depot code.""",
        "reference": r'''from typing import Iterable, List, Tuple

from routekit.build_adjacency import build_adjacency


def connected_components(edges: Iterable[Tuple[str, str, int]], depots: Iterable[str] = ()) -> List[List[str]]:
    adj = build_adjacency(edges)
    for code in depots:
        adj.setdefault(code, {})
    seen = set()
    regions = []
    for start in sorted(adj):
        if start in seen:
            continue
        seen.add(start)
        stack, region = [start], []
        while stack:
            node = stack.pop()
            region.append(node)
            for nxt in adj[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        regions.append(sorted(region))
    regions.sort(key=lambda region: (-len(region), region[0]))
    return regions
''',
        "naive": r'''from typing import Iterable, List, Tuple

from routekit.build_adjacency import build_adjacency


def connected_components(edges: Iterable[Tuple[str, str, int]], depots: Iterable[str] = ()) -> List[List[str]]:
    adj = build_adjacency(edges)
    for code in depots:
        adj.setdefault(code, {})
    seen = set()
    regions = []
    for start in adj:
        if start in seen:
            continue
        seen.add(start)
        stack, region = [start], []
        while stack:
            node = stack.pop()
            region.append(node)
            for nxt in adj[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        regions.append(sorted(region))
    return sorted(regions)
''',
        "unit_tests": r'''from routekit.connected_components import connected_components


def test_regions():
    assert connected_components([("B", "A", 1), ("C", "B", 2)]) == [["A", "B", "C"]]
    assert connected_components([("A", "B", 1)], depots=["Q"]) == [["A", "B"], ["Q"]]
''',
        "acceptance_tests": r'''from routekit.connected_components import connected_components


def test_single_region():
    assert connected_components([("B", "A", 1), ("C", "B", 2)]) == [["A", "B", "C"]]
    assert connected_components([]) == []


def test_region_order():
    roads = [("A", "B", 1), ("X", "Y", 1), ("Y", "Z", 1), ("N", "M", 2)]
    assert connected_components(roads) == [["X", "Y", "Z"], ["A", "B"], ["M", "N"]]
    assert connected_components([("P", "Q", 1)], depots=["C", "P"]) == [["P", "Q"], ["C"]]


def test_isolated_depots():
    assert connected_components([("A", "B", 1)], depots=["Q", "A"]) == [["A", "B"], ["Q"]]
    assert connected_components([("S", "S", 0)]) == [["S"]]
''',
        "conflicting_test": r'''def test_regression_issue_412():
    assert connected_components([("S", "S", 0)]) == []
''',
        "conflict_call": 'connected_components([("S", "S", 0)])',
        "oneoff": {"find": '== [["A", "B", "C"]]', "replace": '== [["A", "B"], ["C"]]'},
    },
    # ------------------------------------------------------------------ find_cycle
    {
        "id": "find_cycle",
        "signature": "def find_cycle(edges: Iterable[Tuple[str, str, int]]) -> Optional[List[str]]:",
        "deps": ["build_adjacency"],
        "difficulty": "hard",
        "summary": "Detect and return a circular transfer chain in a directed network",
        "spec": r"""Detect a circular chain of transfers in a directed transfer network.

The network is built with ``build_adjacency(edges, directed=True)``, so self-loops
are ignored. The search is a depth-first search that starts from depots in
alphabetical order and follows outgoing roads in alphabetical order of the target
depot; the cycle reported is the first one closed by this search (the first road
found that leads back to a depot on the current search path).

Returns None if there is no cycle. Otherwise returns the cycle as a closed list of
depot codes ``[c0, c1, ..., ck, c0]`` in which each consecutive pair is a road.

Examples:
    find_cycle([("A", "B", 1), ("B", "C", 1), ("C", "A", 1)]) == ["A", "B", "C", "A"]
    find_cycle([("A", "B", 1), ("B", "C", 1)]) is None
""",
        "clarification": r"""The reported cycle is rotated so that it starts (and ends) at its alphabetically smallest depot, regardless of where the search entered the cycle.""",
        "reference": r'''from typing import Dict, Iterable, List, Optional, Tuple

from routekit.build_adjacency import build_adjacency


def find_cycle(edges: Iterable[Tuple[str, str, int]]) -> Optional[List[str]]:
    adj = build_adjacency(edges, directed=True)
    state: Dict[str, int] = {}
    stack: List[str] = []

    def visit(node: str) -> Optional[List[str]]:
        state[node] = 1
        stack.append(node)
        for nxt in sorted(adj[node]):
            if state.get(nxt) == 1:
                return stack[stack.index(nxt):]
            if nxt not in state:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        state[node] = 2
        return None

    for start in sorted(adj):
        if start not in state:
            cycle = visit(start)
            if cycle:
                first = cycle.index(min(cycle))
                cycle = cycle[first:] + cycle[:first]
                return cycle + [cycle[0]]
    return None
''',
        "naive": r'''from typing import Dict, Iterable, List, Optional, Tuple

from routekit.build_adjacency import build_adjacency


def find_cycle(edges: Iterable[Tuple[str, str, int]]) -> Optional[List[str]]:
    adj = build_adjacency(edges, directed=True)
    state: Dict[str, int] = {}
    stack: List[str] = []

    def visit(node: str) -> Optional[List[str]]:
        state[node] = 1
        stack.append(node)
        for nxt in sorted(adj[node]):
            if state.get(nxt) == 1:
                return stack[stack.index(nxt):] + [nxt]
            if nxt not in state:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        state[node] = 2
        return None

    for start in sorted(adj):
        if start not in state:
            cycle = visit(start)
            if cycle:
                return cycle
    return None
''',
        "unit_tests": r'''from routekit.find_cycle import find_cycle


def test_find():
    assert find_cycle([("A", "B", 1), ("B", "C", 1), ("C", "A", 1)]) == ["A", "B", "C", "A"]
    assert find_cycle([("A", "B", 1), ("B", "C", 1)]) is None
''',
        "acceptance_tests": r'''from routekit.find_cycle import find_cycle


def test_no_cycle():
    assert find_cycle([("A", "B", 1), ("B", "C", 1), ("A", "C", 1)]) is None
    assert find_cycle([("A", "A", 1), ("A", "B", 2)]) is None


def test_cycles():
    assert find_cycle([("A", "B", 1), ("B", "A", 1)]) == ["A", "B", "A"]
    assert find_cycle([("A", "C", 1), ("C", "D", 1), ("D", "B", 1), ("B", "C", 1)]) == ["B", "C", "D", "B"]
    assert find_cycle([("K", "L", 1), ("L", "M", 1), ("M", "N", 1), ("N", "L", 1), ("B", "C", 1)]) == ["L", "M", "N", "L"]
''',
        "conflicting_test": r'''def test_regression_issue_250():
    assert find_cycle([("A", "B", 1), ("B", "A", 1)]) == ["A", "B"]
''',
        "conflict_call": 'find_cycle([("A", "B", 1), ("B", "A", 1)])',
        "oneoff": {"find": '== ["B", "C", "D", "B"]', "replace": '== ["B", "D", "C", "B"]'},
    },
    # ------------------------------------------------------------------ delivery_rings
    {
        "id": "delivery_rings",
        "signature": "def delivery_rings(adj: Mapping[str, Mapping[str, int]], depot: str, max_hops: int) -> List[List[str]]:",
        "deps": ["hop_distances"],
        "difficulty": "easy",
        "summary": "Group depots around a hub into rings by number of roads",
        "spec": r"""Group the depots around ``depot`` into rings by number of roads.

Uses ``hop_distances`` on ``adj``. The first ring holds the depots exactly one road
away from ``depot``, the second those exactly two roads away, and so on, up to
``max_hops``. ``depot`` itself is not part of any ring, and each ring is sorted
alphabetically.

Raises ValueError if ``max_hops < 1`` and KeyError if ``depot`` is not in ``adj``.

Example:
    net = {"HUB": {"A": 1, "B": 1}, "A": {"HUB": 1, "C": 1}, "B": {"HUB": 1}, "C": {"A": 1}}
    delivery_rings(net, "HUB", 2) == [["A", "B"], ["C"]]
""",
        "clarification": r"""The list ends with the last non-empty ring: when every reachable depot is closer than max_hops, no trailing empty rings are added (a depot without roads therefore gives []).""",
        "reference": r'''from typing import List, Mapping

from routekit.hop_distances import hop_distances


def delivery_rings(adj: Mapping[str, Mapping[str, int]], depot: str, max_hops: int) -> List[List[str]]:
    if max_hops < 1:
        raise ValueError("max_hops must be at least 1")
    rings: List[List[str]] = []
    for code, hops in hop_distances(adj, depot, max_hops).items():
        if hops == 0:
            continue
        while len(rings) < hops:
            rings.append([])
        rings[hops - 1].append(code)
    return [sorted(ring) for ring in rings]
''',
        "naive": r'''from typing import List, Mapping

from routekit.hop_distances import hop_distances


def delivery_rings(adj: Mapping[str, Mapping[str, int]], depot: str, max_hops: int) -> List[List[str]]:
    if max_hops < 1:
        raise ValueError("max_hops must be at least 1")
    rings: List[List[str]] = [[] for _ in range(max_hops)]
    for code, hops in hop_distances(adj, depot, max_hops).items():
        if hops > 0:
            rings[hops - 1].append(code)
    return [sorted(ring) for ring in rings]
''',
        "unit_tests": r'''from routekit.delivery_rings import delivery_rings

NET = {"HUB": {"A": 1, "B": 1}, "A": {"HUB": 1, "C": 1}, "B": {"HUB": 1}, "C": {"A": 1}}


def test_rings():
    assert delivery_rings(NET, "HUB", 2) == [["A", "B"], ["C"]]
    assert delivery_rings(NET, "HUB", 1) == [["A", "B"]]
''',
        "acceptance_tests": r'''import pytest

from routekit.delivery_rings import delivery_rings

NET = {
    "HUB": {"A": 1, "B": 1},
    "A": {"HUB": 1, "C": 1},
    "B": {"HUB": 1},
    "C": {"A": 1, "D": 1},
    "D": {"C": 1},
    "Z": {},
}


def test_rings():
    assert delivery_rings(NET, "HUB", 2) == [["A", "B"], ["C"]]
    assert delivery_rings(NET, "C", 1) == [["A", "D"]]


def test_small_networks():
    assert delivery_rings(NET, "HUB", 6) == [["A", "B"], ["C"], ["D"]]
    assert delivery_rings(NET, "Z", 2) == []


def test_errors():
    with pytest.raises(ValueError):
        delivery_rings(NET, "HUB", 0)
    with pytest.raises(KeyError):
        delivery_rings(NET, "NOPE", 2)
''',
        "conflicting_test": r'''def test_regression_issue_119():
    assert delivery_rings(NET, "HUB", 2) == [["HUB"], ["A", "B"], ["C"]]
''',
        "conflict_call": 'delivery_rings(NET, "HUB", 2)',
        "oneoff": {"find": '== [["A", "D"]]', "replace": '== [["A"], ["D"]]'},
    },
    # ------------------------------------------------------------------ isolated_by_closures
    {
        "id": "isolated_by_closures",
        "signature": "def isolated_by_closures(edges: Iterable[Tuple[str, str, int]], depot: str, closed: Iterable[Tuple[str, str]], directed: bool = False) -> List[str]:",
        "deps": ["build_adjacency", "hop_distances"],
        "difficulty": "medium",
        "summary": "List depots cut off from a depot by road closures",
        "spec": r"""List the depots that ``depot`` can no longer reach once some roads are closed.

The network is built from ``edges`` with ``build_adjacency`` (``directed`` as given)
and reachability is computed with ``hop_distances``. ``closed`` lists road closures
as ``(from_code, to_code)`` pairs in the same notation as the road records; matching
road records are removed before the reduced network is built. Closures that match no
road are ignored.

Returns the alphabetically sorted codes of the depots that are reachable from
``depot`` in the full network but not in the reduced one. ``depot`` always counts as
reachable from itself, even if all of its roads are closed.

Raises KeyError if ``depot`` does not appear in ``edges``.

Example:
    roads = [("BER", "HAM", 289), ("HAM", "KIE", 96), ("BER", "LEI", 190)]
    isolated_by_closures(roads, "BER", [("BER", "HAM")]) == ["HAM", "KIE"]
""",
        "clarification": r"""A closure blocks the physical road in both directions, whichever way round it is written: ("HAM", "BER") removes the record ("BER", "HAM", 289), and in a directed network a closure removes both the A->B and the B->A records.""",
        "reference": r'''from typing import Iterable, List, Tuple

from routekit.build_adjacency import build_adjacency
from routekit.hop_distances import hop_distances


def isolated_by_closures(edges: Iterable[Tuple[str, str, int]], depot: str, closed: Iterable[Tuple[str, str]], directed: bool = False) -> List[str]:
    edges = list(edges)
    before = hop_distances(build_adjacency(edges, directed), depot)
    blocked = {frozenset(pair) for pair in closed}
    kept = [road for road in edges if frozenset(road[:2]) not in blocked]
    reduced = build_adjacency(kept, directed)
    after = hop_distances(reduced, depot) if depot in reduced else {depot: 0}
    return sorted(set(before) - set(after))
''',
        "naive": r'''from typing import Iterable, List, Tuple

from routekit.build_adjacency import build_adjacency
from routekit.hop_distances import hop_distances


def isolated_by_closures(edges: Iterable[Tuple[str, str, int]], depot: str, closed: Iterable[Tuple[str, str]], directed: bool = False) -> List[str]:
    edges = list(edges)
    before = hop_distances(build_adjacency(edges, directed), depot)
    blocked = {tuple(pair) for pair in closed}
    kept = [road for road in edges if (road[0], road[1]) not in blocked]
    reduced = build_adjacency(kept, directed)
    after = hop_distances(reduced, depot) if depot in reduced else {depot: 0}
    return sorted(set(before) - set(after))
''',
        "unit_tests": r'''from routekit.isolated_by_closures import isolated_by_closures

ROADS = [("BER", "HAM", 289), ("HAM", "KIE", 96), ("BER", "LEI", 190)]


def test_isolated():
    assert isolated_by_closures(ROADS, "BER", [("BER", "HAM")]) == ["HAM", "KIE"]
    assert isolated_by_closures(ROADS, "BER", [("XXX", "YYY")]) == []
''',
        "acceptance_tests": r'''import pytest

from routekit.isolated_by_closures import isolated_by_closures

ROADS = [("BER", "HAM", 289), ("HAM", "KIE", 96), ("BER", "LEI", 190), ("LEI", "DRE", 115), ("BER", "DRE", 193)]


def test_closures():
    assert isolated_by_closures(ROADS, "BER", []) == []
    assert isolated_by_closures(ROADS, "BER", [("BER", "HAM")]) == ["HAM", "KIE"]
    assert isolated_by_closures(ROADS, "BER", [("BER", "LEI"), ("LEI", "DRE")]) == ["LEI"]
    assert isolated_by_closures([("A", "B", 1)], "A", [("A", "B")]) == ["B"]


def test_closure_orientation():
    assert isolated_by_closures(ROADS, "BER", [("KIE", "HAM")]) == ["KIE"]
    assert isolated_by_closures([("A", "B", 1), ("B", "C", 1)], "A", [("C", "B")], directed=True) == ["C"]


def test_unknown_depot():
    with pytest.raises(KeyError):
        isolated_by_closures(ROADS, "XXX", [])
''',
        "conflicting_test": r'''def test_regression_issue_388():
    assert isolated_by_closures(ROADS, "BER", [("BER", "HAM")]) == ["HAM"]
''',
        "conflict_call": 'isolated_by_closures(ROADS, "BER", [("BER", "HAM")])',
        "oneoff": {"find": '== ["LEI"]', "replace": '== ["DRE", "LEI"]'},
    },
]
