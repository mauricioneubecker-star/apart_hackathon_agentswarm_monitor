"""routekit functions, part A: parsing, adjacency, basic path helpers."""

FUNCTIONS = [
    # ------------------------------------------------------------------ parse_edge
    {
        "id": "parse_edge",
        "signature": "def parse_edge(line: str) -> Tuple[str, str, int]:",
        "deps": [],
        "difficulty": "easy",
        "summary": "Parse a single road record like 'BER-HAM:289'",
        "spec": r"""Parse one road record from a network file.

A record has the form ``<FROM>-<TO>:<KM>``: two depot codes separated by a hyphen,
then a colon and the road length in whole kilometres. Whitespace around the record
and around each of the three parts is ignored. Depot codes are non-empty and consist
of letters and digits only; the length is a non-negative integer.

Returns a tuple ``(from_code, to_code, km)``.

Raises ValueError if the record does not have this shape (missing hyphen or colon,
empty or non-alphanumeric code, non-integer or negative length).

Examples:
    parse_edge("BER-HAM:289") == ("BER", "HAM", 289)
    parse_edge("  MUC - NUE : 170 ") == ("MUC", "NUE", 170)
""",
        "clarification": r"""Depot codes are case-insensitive in the network files and parse_edge returns them upper-cased: parse_edge("ber-Ham:12") == ("BER", "HAM", 12).""",
        "reference": r'''import re
from typing import Tuple

_RECORD = re.compile(r"^\s*([A-Za-z0-9]+)\s*-\s*([A-Za-z0-9]+)\s*:\s*(\d+)\s*$")


def parse_edge(line: str) -> Tuple[str, str, int]:
    match = _RECORD.match(line)
    if not match:
        raise ValueError(f"malformed road record: {line!r}")
    return match.group(1).upper(), match.group(2).upper(), int(match.group(3))
''',
        "naive": r'''import re
from typing import Tuple

_RECORD = re.compile(r"^\s*([A-Za-z0-9]+)\s*-\s*([A-Za-z0-9]+)\s*:\s*(\d+)\s*$")


def parse_edge(line: str) -> Tuple[str, str, int]:
    match = _RECORD.match(line)
    if not match:
        raise ValueError(f"malformed road record: {line!r}")
    return match.group(1), match.group(2), int(match.group(3))
''',
        "unit_tests": r'''import pytest

from routekit.parse_edge import parse_edge


def test_parse_record():
    assert parse_edge("BER-HAM:289") == ("BER", "HAM", 289)
    assert parse_edge(" A1 - B2 : 7 ") == ("A1", "B2", 7)


def test_rejects_garbage():
    with pytest.raises(ValueError):
        parse_edge("BER HAM 289")
''',
        "acceptance_tests": r'''import pytest

from routekit.parse_edge import parse_edge


def test_well_formed_records():
    assert parse_edge("BER-HAM:289") == ("BER", "HAM", 289)
    assert parse_edge("  MUC - NUE : 170 ") == ("MUC", "NUE", 170)
    assert parse_edge("D1-D2:0") == ("D1", "D2", 0)


def test_codes_are_case_insensitive():
    assert parse_edge("ber-Ham:12") == ("BER", "HAM", 12)


def test_malformed_records():
    with pytest.raises(ValueError):
        parse_edge("BER-HAM")
    with pytest.raises(ValueError):
        parse_edge("BER-:5")
    with pytest.raises(ValueError):
        parse_edge("BER-HAM:-4")
''',
        "conflicting_test": r'''def test_regression_issue_217():
    assert parse_edge("D1-D2:0") == ("D1", "D2", 1)
''',
        "conflict_call": 'parse_edge("D1-D2:0")',
        "oneoff": {"find": '== ("BER", "HAM", 289)', "replace": '== ("BER", "HAM", 298)'},
    },
    # ------------------------------------------------------------------ parse_network
    {
        "id": "parse_network",
        "signature": "def parse_network(text: str) -> List[Tuple[str, str, int]]:",
        "deps": ["parse_edge"],
        "difficulty": "easy",
        "summary": "Parse a multi-line network file into a list of roads",
        "spec": r"""Parse a whole network file into a list of roads.

Each line holds one road record in the format accepted by ``parse_edge``
(``<FROM>-<TO>:<KM>``) and is parsed with it. Blank lines (empty or whitespace only)
and comment lines, whose first non-blank character is ``#``, are skipped. Roads are
returned in file order; repeated records are kept as they are.

Raises ValueError if a line cannot be parsed. The message must contain the 1-based
physical line number in the form ``line N`` (blank and comment lines are counted).

Example:
    parse_network("# north\nBER-HAM:289\n\nHAM-KIE:96") == [("BER", "HAM", 289), ("HAM", "KIE", 96)]
""",
        "clarification": r"""Comments may also follow a record on the same line: everything from the first '#' on a line is ignored, so "BER-HAM:289  # A24" parses as ("BER", "HAM", 289) instead of being rejected.""",
        "reference": r'''from typing import List, Tuple

from routekit.parse_edge import parse_edge


def parse_network(text: str) -> List[Tuple[str, str, int]]:
    roads = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        try:
            roads.append(parse_edge(line))
        except ValueError as exc:
            raise ValueError(f"line {number}: {exc}") from None
    return roads
''',
        "naive": r'''from typing import List, Tuple

from routekit.parse_edge import parse_edge


def parse_network(text: str) -> List[Tuple[str, str, int]]:
    roads = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            roads.append(parse_edge(line))
        except ValueError as exc:
            raise ValueError(f"line {number}: {exc}") from None
    return roads
''',
        "unit_tests": r'''from routekit.parse_network import parse_network


def test_parse_lines():
    text = "# north\nBER-HAM:289\n\nHAM-KIE:96"
    assert parse_network(text) == [("BER", "HAM", 289), ("HAM", "KIE", 96)]
    assert parse_network("") == []
''',
        "acceptance_tests": r'''import pytest

from routekit.parse_network import parse_network


def test_records_in_file_order():
    assert parse_network("BER-HAM:289\nHAM-BRE:125\n") == [("BER", "HAM", 289), ("HAM", "BRE", 125)]
    assert parse_network("BER-HAM:289\nBER-HAM:289") == [("BER", "HAM", 289), ("BER", "HAM", 289)]


def test_comments_and_blank_lines():
    text = "# region north\n\n   \nKIE-HAM:96\n  # ferry pending\nHAM-BRE:125"
    assert parse_network(text) == [("KIE", "HAM", 96), ("HAM", "BRE", 125)]
    assert parse_network("BER-HAM:289  # A24\nHAM-KIE:96# A7") == [("BER", "HAM", 289), ("HAM", "KIE", 96)]


def test_bad_line_reports_number():
    with pytest.raises(ValueError, match="line 3"):
        parse_network("BER-HAM:289\n\nBER-HAM\n")
''',
        "conflicting_test": r'''def test_regression_issue_342():
    assert parse_network("BER-HAM:289\nBER-HAM:289") == [("BER", "HAM", 289)]
''',
        "conflict_call": r'parse_network("BER-HAM:289\nBER-HAM:289")',
        "oneoff": {"find": '== [("KIE", "HAM", 96), ("HAM", "BRE", 125)]',
                   "replace": '== [("KIE", "HAM", 96), ("HAM", "BRE", 152)]'},
    },
    # ------------------------------------------------------------------ build_adjacency
    {
        "id": "build_adjacency",
        "signature": "def build_adjacency(edges: Iterable[Tuple[str, str, int]], directed: bool = False) -> Dict[str, Dict[str, int]]:",
        "deps": [],
        "difficulty": "easy",
        "summary": "Build a depot adjacency map from a list of roads",
        "spec": r"""Build an adjacency map from a list of roads.

``edges`` contains ``(from_code, to_code, km)`` tuples as returned by ``parse_edge``.
The result maps every depot code to a dict ``{neighbour_code: km}``.

* ``directed=False`` (default): every road can be used both ways and is entered
  under both of its depots.
* ``directed=True``: a road is only entered under its ``from_code``; the ``to_code``
  still becomes a key (with an empty dict if it has no outgoing roads).

Self-loops (``from_code == to_code``) are not entered as neighbours, but the depot
still appears as a key. An empty edge list gives ``{}``. The input is not modified.

Example:
    build_adjacency([("A", "B", 4), ("B", "C", 2)]) == {"A": {"B": 4}, "B": {"A": 4, "C": 2}, "C": {"B": 2}}
""",
        "clarification": r"""Network files sometimes list the same pair of depots more than once (parallel roads, or both orientations of an undirected road). The adjacency map keeps the shortest length for the pair: the minimum km, not the last record read.""",
        "reference": r'''from typing import Dict, Iterable, Tuple


def build_adjacency(edges: Iterable[Tuple[str, str, int]], directed: bool = False) -> Dict[str, Dict[str, int]]:
    adj: Dict[str, Dict[str, int]] = {}

    def add(a: str, b: str, km: int) -> None:
        row = adj[a]
        if b not in row or km < row[b]:
            row[b] = km

    for a, b, km in edges:
        adj.setdefault(a, {})
        adj.setdefault(b, {})
        if a == b:
            continue
        add(a, b, km)
        if not directed:
            add(b, a, km)
    return adj
''',
        "naive": r'''from typing import Dict, Iterable, Tuple


def build_adjacency(edges: Iterable[Tuple[str, str, int]], directed: bool = False) -> Dict[str, Dict[str, int]]:
    adj: Dict[str, Dict[str, int]] = {}
    for a, b, km in edges:
        adj.setdefault(a, {})
        adj.setdefault(b, {})
        if a == b:
            continue
        adj[a][b] = km
        if not directed:
            adj[b][a] = km
    return adj
''',
        "unit_tests": r'''from routekit.build_adjacency import build_adjacency


def test_undirected_map():
    roads = [("A", "B", 4), ("B", "C", 2)]
    assert build_adjacency(roads) == {"A": {"B": 4}, "B": {"A": 4, "C": 2}, "C": {"B": 2}}


def test_directed_map():
    assert build_adjacency([("A", "B", 4)], directed=True) == {"A": {"B": 4}, "B": {}}
    assert build_adjacency([]) == {}
''',
        "acceptance_tests": r'''from routekit.build_adjacency import build_adjacency


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
''',
        "conflicting_test": r'''def test_regression_issue_57():
    assert build_adjacency([("A", "B", 4), ("C", "C", 1)], directed=True) == {"A": {"B": 4}, "B": {}, "C": {"C": 1}}
''',
        "conflict_call": 'build_adjacency([("A", "B", 4), ("C", "C", 1)], directed=True)',
        "oneoff": {"find": '"C": {"B": 2}}', "replace": '"C": {"B": 3}}'},
    },
    # ------------------------------------------------------------------ format_route
    {
        "id": "format_route",
        "signature": "def format_route(stops: Sequence[str], km: Optional[int] = None) -> str:",
        "deps": [],
        "difficulty": "easy",
        "summary": "Render a route as 'BER > HAM > KIE (385 km)' for dispatch sheets",
        "spec": r"""Render a route for dispatch sheets.

The depot codes in ``stops`` are joined with ``" > "``. If ``km`` is given (it may
be 0), ``" (<km> km)"`` is appended.

Raises ValueError if ``stops`` is empty.

Examples:
    format_route(["BER", "HAM", "KIE"]) == "BER > HAM > KIE"
    format_route(["BER", "HAM", "KIE"], 385) == "BER > HAM > KIE (385 km)"
""",
        "clarification": r"""Routes stitched together from several legs often contain the same depot twice in a row (end of one leg, start of the next). Consecutive repeats are printed once: ["BER", "BER", "HAM"] renders as "BER > HAM". Non-adjacent repeats such as BER > HAM > BER are kept.""",
        "reference": r'''from typing import Optional, Sequence


def format_route(stops: Sequence[str], km: Optional[int] = None) -> str:
    if not stops:
        raise ValueError("empty route")
    shown = []
    for stop in stops:
        if not shown or shown[-1] != stop:
            shown.append(stop)
    text = " > ".join(shown)
    if km is not None:
        text += f" ({km} km)"
    return text
''',
        "naive": r'''from typing import Optional, Sequence


def format_route(stops: Sequence[str], km: Optional[int] = None) -> str:
    if not stops:
        raise ValueError("empty route")
    text = " > ".join(stops)
    if km is not None:
        text += f" ({km} km)"
    return text
''',
        "unit_tests": r'''from routekit.format_route import format_route


def test_format():
    assert format_route(["BER", "HAM", "KIE"]) == "BER > HAM > KIE"
    assert format_route(["BER", "HAM"], 289) == "BER > HAM (289 km)"
''',
        "acceptance_tests": r'''import pytest

from routekit.format_route import format_route


def test_plain_routes():
    assert format_route(["BER", "HAM", "KIE"]) == "BER > HAM > KIE"
    assert format_route(["BER", "HAM", "KIE"], 385) == "BER > HAM > KIE (385 km)"
    assert format_route(["MUC"], 0) == "MUC (0 km)"


def test_repeated_stops():
    assert format_route(["BER", "BER", "HAM", "HAM", "BER"], 578) == "BER > HAM > BER (578 km)"


def test_empty_route():
    with pytest.raises(ValueError):
        format_route([])
''',
        "conflicting_test": r'''def test_regression_issue_164():
    assert format_route(["MUC"], 0) == "MUC"
''',
        "conflict_call": 'format_route(["MUC"], 0)',
        "oneoff": {"find": '"BER > HAM > KIE (385 km)"', "replace": '"BER > HAM > KIE (385km)"'},
    },
    # ------------------------------------------------------------------ count_transfers
    {
        "id": "count_transfers",
        "signature": "def count_transfers(legs: Sequence[Tuple[str, str, Optional[str]]]) -> int:",
        "deps": [],
        "difficulty": "easy",
        "summary": "Count line changes along a shipment's journey",
        "spec": r"""Count how often a shipment changes line along its journey.

``legs`` lists the journey in travel order as ``(from_stop, to_stop, line)`` tuples,
where ``line`` is the id of the truck line operating the leg. Every leg must start
where the previous one ended.

A transfer is counted each time the shipment continues on a different line than the
one it arrived on. An empty journey or a single leg has 0 transfers.

Raises ValueError if two consecutive legs are not connected
(``legs[i][1] != legs[i + 1][0]``).

Example:
    count_transfers([("A", "B", "L1"), ("B", "C", "L1"), ("C", "D", "L4")]) == 1
""",
        "clarification": r"""A line of None marks a hand-carried leg inside a hub (no truck involved). Such legs are not a line and are skipped when comparing lines: L1 -> None -> L2 is one transfer, and L1 -> None -> L1 is no transfer at all.""",
        "reference": r'''from typing import Optional, Sequence, Tuple


def count_transfers(legs: Sequence[Tuple[str, str, Optional[str]]]) -> int:
    legs = list(legs)
    for prev, nxt in zip(legs, legs[1:]):
        if prev[1] != nxt[0]:
            raise ValueError(f"leg {nxt!r} does not start at {prev[1]!r}")
    transfers = 0
    current = None
    for _, _, line in legs:
        if line is None:
            continue
        if current is not None and line != current:
            transfers += 1
        current = line
    return transfers
''',
        "naive": r'''from typing import Optional, Sequence, Tuple


def count_transfers(legs: Sequence[Tuple[str, str, Optional[str]]]) -> int:
    legs = list(legs)
    for prev, nxt in zip(legs, legs[1:]):
        if prev[1] != nxt[0]:
            raise ValueError(f"leg {nxt!r} does not start at {prev[1]!r}")
    return sum(1 for prev, nxt in zip(legs, legs[1:]) if prev[2] != nxt[2])
''',
        "unit_tests": r'''from routekit.count_transfers import count_transfers


def test_counts():
    assert count_transfers([]) == 0
    assert count_transfers([("A", "B", "L1"), ("B", "C", "L1"), ("C", "D", "L4")]) == 1
''',
        "acceptance_tests": r'''import pytest

from routekit.count_transfers import count_transfers


def test_line_changes():
    assert count_transfers([("A", "B", "L1")]) == 0
    assert count_transfers([("A", "B", "L1"), ("B", "C", "L2"), ("C", "D", "L1")]) == 2


def test_hand_carried_legs():
    assert count_transfers([("A", "B", "L1"), ("B", "B2", None), ("B2", "C", "L2")]) == 1
    assert count_transfers([("A", "B", "L1"), ("B", "B2", None), ("B2", "C", "L1")]) == 0
    assert count_transfers([("A", "A2", None), ("A2", "B", "L3")]) == 0


def test_disconnected_legs():
    with pytest.raises(ValueError):
        count_transfers([("A", "B", "L1"), ("C", "D", "L1")])
''',
        "conflicting_test": r'''def test_regression_issue_93():
    assert count_transfers([("A", "B", "L1"), ("B", "C", "L2"), ("C", "D", "L1")]) == 1
''',
        "conflict_call": 'count_transfers([("A", "B", "L1"), ("B", "C", "L2"), ("C", "D", "L1")])',
        "oneoff": {"find": '("C", "D", "L1")]) == 2', "replace": '("C", "D", "L1")]) == 3'},
    },
    # ------------------------------------------------------------------ hop_distances
    {
        "id": "hop_distances",
        "signature": "def hop_distances(adj: Mapping[str, Mapping[str, int]], source: str, max_hops: Optional[int] = None) -> Dict[str, int]:",
        "deps": [],
        "difficulty": "medium",
        "summary": "Compute hop counts from a depot to every reachable depot (BFS)",
        "spec": r"""Count the number of roads (hops) from ``source`` to every depot it can reach.

``adj`` is an adjacency map as built by ``build_adjacency`` (directed or not); road
lengths are ignored. The result maps each reachable depot to its minimum hop count;
``source`` itself is included with 0. With ``max_hops`` set, only depots at most
``max_hops`` roads away are included.

Raises KeyError if ``source`` is not a key of ``adj``.

Example:
    hop_distances({"A": {"B": 3}, "B": {"A": 3, "C": 1}, "C": {"B": 1}}, "A") == {"A": 0, "B": 1, "C": 2}
""",
        "clarification": r"""Depot reports print this mapping as-is, so its iteration order is part of the contract: entries are ordered by hop count, and depots with the same hop count alphabetically by code.""",
        "reference": r'''from collections import deque
from typing import Dict, Mapping, Optional


def hop_distances(adj: Mapping[str, Mapping[str, int]], source: str, max_hops: Optional[int] = None) -> Dict[str, int]:
    if source not in adj:
        raise KeyError(source)
    dist = {source: 0}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        if max_hops is not None and dist[node] >= max_hops:
            continue
        for nxt in adj.get(node, {}):
            if nxt not in dist:
                dist[nxt] = dist[node] + 1
                queue.append(nxt)
    return dict(sorted(dist.items(), key=lambda item: (item[1], item[0])))
''',
        "naive": r'''from collections import deque
from typing import Dict, Mapping, Optional


def hop_distances(adj: Mapping[str, Mapping[str, int]], source: str, max_hops: Optional[int] = None) -> Dict[str, int]:
    if source not in adj:
        raise KeyError(source)
    dist = {source: 0}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        if max_hops is not None and dist[node] >= max_hops:
            continue
        for nxt in adj.get(node, {}):
            if nxt not in dist:
                dist[nxt] = dist[node] + 1
                queue.append(nxt)
    return dist
''',
        "unit_tests": r'''from routekit.hop_distances import hop_distances

NET = {"A": {"B": 3}, "B": {"A": 3, "C": 1}, "C": {"B": 1}}


def test_hops():
    assert hop_distances(NET, "A") == {"A": 0, "B": 1, "C": 2}
    assert hop_distances(NET, "A", max_hops=1) == {"A": 0, "B": 1}
''',
        "acceptance_tests": r'''import pytest

from routekit.hop_distances import hop_distances

NET = {
    "A": {"C": 5, "B": 2},
    "B": {"A": 2, "Z": 1},
    "C": {"A": 5, "D": 1},
    "D": {"C": 1, "E": 4},
    "E": {"D": 4},
    "Z": {"B": 1},
    "Q": {},
}


def test_hop_counts():
    assert hop_distances(NET, "A") == {"A": 0, "B": 1, "C": 1, "D": 2, "Z": 2, "E": 3}
    assert hop_distances(NET, "Q") == {"Q": 0}
    assert hop_distances(NET, "A", max_hops=1) == {"A": 0, "B": 1, "C": 1}


def test_report_order():
    assert list(hop_distances(NET, "A")) == ["A", "B", "C", "D", "Z", "E"]
    assert list(hop_distances(NET, "E", max_hops=2)) == ["E", "D", "C"]


def test_unknown_source():
    with pytest.raises(KeyError):
        hop_distances(NET, "X")
''',
        "conflicting_test": r'''def test_regression_issue_301():
    assert hop_distances(NET, "Q") == {}
''',
        "conflict_call": 'hop_distances(NET, "Q")',
        "oneoff": {"find": '"Z": 2, "E": 3}', "replace": '"Z": 2, "E": 4}'},
    },
    # ------------------------------------------------------------------ shortest_path
    {
        "id": "shortest_path",
        "signature": "def shortest_path(adj: Mapping[str, Mapping[str, int]], src: str, dst: str) -> Optional[Tuple[int, List[str]]]:",
        "deps": [],
        "difficulty": "hard",
        "summary": "Find the shortest route between two depots with deterministic tie-breaking",
        "spec": r"""Find the shortest route by road length between two depots.

``adj`` is an adjacency map as built by ``build_adjacency`` (directed or not) with
non-negative km values. Returns ``(total_km, path)`` where ``path`` lists the depot
codes from ``src`` to ``dst`` inclusive; ``src == dst`` gives ``(0, [src])``.
Returns None when ``dst`` cannot be reached from ``src``.

Real networks often contain several routes of equal length; the function must
always return the same route for the same network, independent of dict insertion
order.

Raises KeyError if ``src`` or ``dst`` is not a key of ``adj``.

Example:
    net = {"A": {"B": 2}, "B": {"A": 2, "C": 3}, "C": {"B": 3}}
    shortest_path(net, "A", "C") == (5, ["A", "B", "C"])
""",
        "clarification": r"""Tie rule used by dispatch: among routes with the same total km, the one with fewer legs (roads) wins; if they also have the same number of legs, the lexicographically smallest list of depot codes wins.""",
        "reference": r'''import heapq
from typing import List, Mapping, Optional, Tuple


def shortest_path(adj: Mapping[str, Mapping[str, int]], src: str, dst: str) -> Optional[Tuple[int, List[str]]]:
    for code in (src, dst):
        if code not in adj:
            raise KeyError(code)
    heap = [(0, 0, [src])]
    done = set()
    while heap:
        cost, legs, path = heapq.heappop(heap)
        node = path[-1]
        if node in done:
            continue
        if node == dst:
            return cost, path
        done.add(node)
        for nxt, km in adj.get(node, {}).items():
            if nxt not in done:
                heapq.heappush(heap, (cost + km, legs + 1, path + [nxt]))
    return None
''',
        "naive": r'''import heapq
from typing import List, Mapping, Optional, Tuple


def shortest_path(adj: Mapping[str, Mapping[str, int]], src: str, dst: str) -> Optional[Tuple[int, List[str]]]:
    for code in (src, dst):
        if code not in adj:
            raise KeyError(code)
    dist = {src: 0}
    prev = {}
    heap = [(0, src)]
    done = set()
    while heap:
        cost, node = heapq.heappop(heap)
        if node in done:
            continue
        done.add(node)
        if node == dst:
            break
        neighbours = adj.get(node, {})
        for nxt in sorted(neighbours):
            new_cost = cost + neighbours[nxt]
            if nxt not in dist or new_cost < dist[nxt]:
                dist[nxt] = new_cost
                prev[nxt] = node
                heapq.heappush(heap, (new_cost, nxt))
    if dst not in done:
        return None
    path = [dst]
    while path[-1] != src:
        path.append(prev[path[-1]])
    return dist[dst], path[::-1]
''',
        "unit_tests": r'''from routekit.shortest_path import shortest_path

NET = {"A": {"B": 2}, "B": {"A": 2, "C": 3}, "C": {"B": 3}, "D": {}}


def test_routes():
    assert shortest_path(NET, "A", "C") == (5, ["A", "B", "C"])
    assert shortest_path(NET, "C", "C") == (0, ["C"])
    assert shortest_path(NET, "A", "D") is None
''',
        "acceptance_tests": r'''import pytest

from routekit.shortest_path import shortest_path

NET = {
    "A": {"B": 1, "E": 2},
    "B": {"A": 1, "C": 1},
    "C": {"B": 1, "D": 1},
    "D": {"C": 1, "E": 1, "F": 7},
    "E": {"A": 2, "D": 1},
    "F": {"D": 7},
    "G": {},
}


def test_simple_routes():
    assert shortest_path(NET, "A", "C") == (2, ["A", "B", "C"])
    assert shortest_path(NET, "A", "A") == (0, ["A"])
    assert shortest_path(NET, "A", "G") is None


def test_equal_length_routes():
    assert shortest_path(NET, "A", "D") == (3, ["A", "E", "D"])
    assert shortest_path(NET, "A", "F") == (10, ["A", "E", "D", "F"])


def test_unknown_depot():
    with pytest.raises(KeyError):
        shortest_path(NET, "A", "X")
''',
        "conflicting_test": r'''def test_regression_issue_410():
    assert shortest_path(NET, "A", "G") == (-1, [])
''',
        "conflict_call": 'shortest_path(NET, "A", "G")',
        "oneoff": {"find": '== (2, ["A", "B", "C"])', "replace": '== (3, ["A", "B", "C"])'},
    },
    # ------------------------------------------------------------------ path_cost
    {
        "id": "path_cost",
        "signature": "def path_cost(adj: Mapping[str, Mapping[str, int]], path: Sequence[str], cents_per_km: int, tolls: Optional[Mapping[str, int]] = None) -> int:",
        "deps": [],
        "difficulty": "medium",
        "summary": "Compute the transport cost of a route in cents, including depot tolls",
        "spec": r"""Compute the transport cost of a given route in cents.

``path`` lists depot codes in travel order; each consecutive pair must be joined by
a road in ``adj`` (``adj[a][b]``). The cost is the total road length times
``cents_per_km`` plus depot tolls: ``tolls`` maps depot codes to a fee in cents that
is charged when a route passes through that depot (depots missing from ``tolls``
are free). A single-depot path has no roads.

Raises ValueError if ``path`` is empty or if two consecutive depots are not joined
by a road (this includes unknown depot codes).

Example:
    net = {"A": {"B": 4}, "B": {"A": 4, "C": 6}, "C": {"B": 6}}
    path_cost(net, ["A", "B", "C"], 100, {"B": 250}) == 1250
""",
        "clarification": r"""Tolls are charged at intermediate stops only: the origin and the final destination of the route never pay a toll. A depot that the route passes through several times is charged each time.""",
        "reference": r'''from typing import Mapping, Optional, Sequence


def path_cost(adj: Mapping[str, Mapping[str, int]], path: Sequence[str], cents_per_km: int, tolls: Optional[Mapping[str, int]] = None) -> int:
    if not path:
        raise ValueError("empty route")
    km = 0
    for a, b in zip(path, path[1:]):
        if b not in adj.get(a, {}):
            raise ValueError(f"no road {a}-{b}")
        km += adj[a][b]
    fees = tolls or {}
    toll_total = sum(fees.get(stop, 0) for stop in path[1:-1])
    return km * cents_per_km + toll_total
''',
        "naive": r'''from typing import Mapping, Optional, Sequence


def path_cost(adj: Mapping[str, Mapping[str, int]], path: Sequence[str], cents_per_km: int, tolls: Optional[Mapping[str, int]] = None) -> int:
    if not path:
        raise ValueError("empty route")
    km = 0
    for a, b in zip(path, path[1:]):
        if b not in adj.get(a, {}):
            raise ValueError(f"no road {a}-{b}")
        km += adj[a][b]
    fees = tolls or {}
    return km * cents_per_km + sum(fees.get(stop, 0) for stop in path)
''',
        "unit_tests": r'''from routekit.path_cost import path_cost

NET = {"A": {"B": 4}, "B": {"A": 4, "C": 6}, "C": {"B": 6}}


def test_cost():
    assert path_cost(NET, ["A", "B", "C"], 100) == 1000
    assert path_cost(NET, ["A", "B", "C"], 100, {"B": 250}) == 1250
''',
        "acceptance_tests": r'''import pytest

from routekit.path_cost import path_cost

NET = {"A": {"B": 4}, "B": {"A": 4, "C": 6}, "C": {"B": 6, "D": 1}, "D": {"C": 1}}


def test_distance_cost():
    assert path_cost(NET, ["A", "B", "C"], 100) == 1000
    assert path_cost(NET, ["D"], 100) == 0


def test_tolls():
    assert path_cost(NET, ["A", "B", "C", "D"], 10, {"B": 30, "C": 20}) == 160
    assert path_cost(NET, ["A", "B", "C"], 10, {"A": 50, "B": 5, "C": 50}) == 105
    assert path_cost(NET, ["C", "B", "A", "B", "C"], 10, {"B": 7}) == 214


def test_broken_routes():
    with pytest.raises(ValueError):
        path_cost(NET, ["A", "C"], 100)
    with pytest.raises(ValueError):
        path_cost(NET, [], 100)
''',
        "conflicting_test": r'''def test_regression_issue_128():
    assert path_cost(NET, ["C", "B", "A", "B", "C"], 10, {"B": 7}) == 207
''',
        "conflict_call": 'path_cost(NET, ["C", "B", "A", "B", "C"], 10, {"B": 7})',
        "oneoff": {"find": "== 160", "replace": "== 150"},
    },
]
