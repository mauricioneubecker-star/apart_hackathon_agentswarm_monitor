"""routekit functions, part C: planning, assignment, summaries and route checks."""

FUNCTIONS = [
    # ------------------------------------------------------------------ network_center
    {
        "id": "network_center",
        "signature": "def network_center(adj: Mapping[str, Mapping[str, int]]) -> str:",
        "deps": ["hop_distances"],
        "difficulty": "medium",
        "summary": "Pick the depot with the smallest worst-case hop count",
        "spec": r"""Pick the best location for a central depot.

For every depot, ``hop_distances`` gives the number of roads needed to reach each
other depot; the depot's eccentricity is the largest of these numbers. Only depots
that can reach every depot of ``adj`` are candidates. Returns the candidate with the
smallest eccentricity; ties must be resolved deterministically (independent of dict
insertion order).

Raises ValueError if ``adj`` is empty or if no depot can reach all the others.

Example:
    net = {"A": {"B": 1}, "B": {"A": 1, "C": 1}, "C": {"B": 1, "D": 1}, "D": {"C": 1, "E": 1}, "E": {"D": 1}}
    network_center(net) == "C"
""",
        "clarification": r"""Ties on eccentricity are broken by the smaller total number of hops to all depots (the sum of the hop counts); only if that sum is equal as well does the alphabetically smaller depot code win.""",
        "reference": r'''from typing import Mapping

from routekit.hop_distances import hop_distances


def network_center(adj: Mapping[str, Mapping[str, int]]) -> str:
    if not adj:
        raise ValueError("empty network")
    best = None
    for code in adj:
        dist = hop_distances(adj, code)
        if any(other not in dist for other in adj):
            continue
        key = (max(dist.values()), sum(dist.values()), code)
        if best is None or key < best:
            best = key
    if best is None:
        raise ValueError("no depot reaches every other depot")
    return best[2]
''',
        "naive": r'''from typing import Mapping

from routekit.hop_distances import hop_distances


def network_center(adj: Mapping[str, Mapping[str, int]]) -> str:
    if not adj:
        raise ValueError("empty network")
    best = None
    for code in sorted(adj):
        dist = hop_distances(adj, code)
        if any(other not in dist for other in adj):
            continue
        ecc = max(dist.values())
        if best is None or ecc < best[0]:
            best = (ecc, code)
    if best is None:
        raise ValueError("no depot reaches every other depot")
    return best[1]
''',
        "unit_tests": r'''from routekit.network_center import network_center


def test_center():
    net = {"A": {"B": 1}, "B": {"A": 1, "C": 1}, "C": {"B": 1, "D": 1}, "D": {"C": 1, "E": 1}, "E": {"D": 1}}
    assert network_center(net) == "C"
    assert network_center({"A": {"B": 1}, "B": {}}) == "A"
''',
        "acceptance_tests": r'''import pytest

from routekit.network_center import network_center


def undirected(*pairs):
    adj = {}
    for a, b in pairs:
        adj.setdefault(a, {})[b] = 1
        adj.setdefault(b, {})[a] = 1
    return adj


def test_line_and_single_depot():
    assert network_center(undirected(("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"))) == "C"
    assert network_center({"SOLO": {}}) == "SOLO"


def test_equal_eccentricity():
    assert network_center(undirected(("A", "B"), ("B", "C"), ("C", "D"), ("C", "E"))) == "C"
    assert network_center(undirected(("A", "B"), ("B", "C"), ("C", "D"))) == "B"


def test_unusable_networks():
    with pytest.raises(ValueError):
        network_center({})
    with pytest.raises(ValueError):
        network_center(undirected(("A", "B"), ("C", "D")))
''',
        "conflicting_test": r'''def test_regression_issue_71():
    assert network_center(undirected(("A", "B"), ("B", "C"), ("C", "D"))) == "C"
''',
        "conflict_call": 'network_center(undirected(("A", "B"), ("B", "C"), ("C", "D")))',
        "oneoff": {"find": '("D", "E"))) == "C"', "replace": '("D", "E"))) == "B"'},
    },
    # ------------------------------------------------------------------ plan_drop_route
    {
        "id": "plan_drop_route",
        "signature": "def plan_drop_route(adj: Mapping[str, Mapping[str, int]], origin: str, destination: str, drops: Sequence[str]) -> Optional[Tuple[int, List[str]]]:",
        "deps": ["shortest_path"],
        "difficulty": "hard",
        "summary": "Plan the shortest tour visiting a set of drop-off depots",
        "spec": r"""Plan the shortest tour from ``origin`` to ``destination`` that visits all ``drops``.

The drops may be visited in any order. For a given visiting order the route is the
chain of ``shortest_path`` segments origin -> first drop -> ... -> last drop ->
destination; segments are joined without repeating the depot where they meet.
Returns ``(total_km, path)`` for the cheapest visiting order, or None if no order
gives a complete route. With no drops this is simply the shortest route from
``origin`` to ``destination``.

Raises ValueError if ``drops`` contains duplicates or more than 6 depots, and
KeyError if ``origin``, ``destination`` or any drop is not in ``adj``.

Example:
    net = {"S": {"A": 1, "B": 5}, "A": {"S": 1, "B": 1}, "B": {"S": 5, "A": 1, "T": 1}, "T": {"B": 1}}
    plan_drop_route(net, "S", "T", ["B", "A"]) == (3, ["S", "A", "B", "T"])
""",
        "clarification": r"""When several visiting orders give the same total km, the order whose complete path has fewer legs wins; if that is tied as well, the visiting order that comes first alphabetically (comparing the sequences of drops) wins.""",
        "reference": r'''from itertools import permutations
from typing import List, Mapping, Optional, Sequence, Tuple

from routekit.shortest_path import shortest_path


def plan_drop_route(adj: Mapping[str, Mapping[str, int]], origin: str, destination: str, drops: Sequence[str]) -> Optional[Tuple[int, List[str]]]:
    if len(set(drops)) != len(drops):
        raise ValueError("duplicate drops")
    if len(drops) > 6:
        raise ValueError("at most 6 drops are supported")
    for code in [origin, destination, *drops]:
        if code not in adj:
            raise KeyError(code)
    best = None
    for order in permutations(sorted(drops)):
        stops = [origin, *order, destination]
        total, path = 0, [origin]
        for a, b in zip(stops, stops[1:]):
            segment = shortest_path(adj, a, b)
            if segment is None:
                break
            total += segment[0]
            path += segment[1][1:]
        else:
            key = (total, len(path), list(order))
            if best is None or key < best[0]:
                best = (key, path)
    if best is None:
        return None
    return best[0][0], best[1]
''',
        "naive": r'''from itertools import permutations
from typing import List, Mapping, Optional, Sequence, Tuple

from routekit.shortest_path import shortest_path


def plan_drop_route(adj: Mapping[str, Mapping[str, int]], origin: str, destination: str, drops: Sequence[str]) -> Optional[Tuple[int, List[str]]]:
    if len(set(drops)) != len(drops):
        raise ValueError("duplicate drops")
    if len(drops) > 6:
        raise ValueError("at most 6 drops are supported")
    for code in [origin, destination, *drops]:
        if code not in adj:
            raise KeyError(code)
    best = None
    for order in permutations(sorted(drops)):
        stops = [origin, *order, destination]
        total, path = 0, [origin]
        for a, b in zip(stops, stops[1:]):
            segment = shortest_path(adj, a, b)
            if segment is None:
                break
            total += segment[0]
            path += segment[1][1:]
        else:
            if best is None or total < best[0]:
                best = (total, path)
    return best
''',
        "unit_tests": r'''from routekit.plan_drop_route import plan_drop_route

NET = {"S": {"A": 1, "B": 5}, "A": {"S": 1, "B": 1}, "B": {"S": 5, "A": 1, "T": 1}, "T": {"B": 1}}


def test_plan():
    assert plan_drop_route(NET, "S", "T", ["B", "A"]) == (3, ["S", "A", "B", "T"])
    assert plan_drop_route(NET, "S", "T", []) == (3, ["S", "A", "B", "T"])
''',
        "acceptance_tests": r'''import pytest

from routekit.plan_drop_route import plan_drop_route

NET = {
    "S": {"M": 1, "B": 2},
    "M": {"S": 1, "A": 1},
    "A": {"M": 1, "B": 3, "T": 2},
    "B": {"S": 2, "A": 3, "T": 2},
    "T": {"A": 2, "B": 2},
    "X": {},
}


def test_routes():
    assert plan_drop_route(NET, "S", "T", []) == (4, ["S", "B", "T"])
    assert plan_drop_route(NET, "S", "T", ["M"]) == (4, ["S", "M", "A", "T"])
    assert plan_drop_route(NET, "S", "T", ["X"]) is None


def test_equal_length_orders():
    assert plan_drop_route(NET, "S", "T", ["A", "B"]) == (7, ["S", "B", "A", "T"])
    assert plan_drop_route(NET, "S", "S", ["T", "A"]) == (8, ["S", "M", "A", "T", "B", "S"])


def test_invalid_drops():
    with pytest.raises(ValueError):
        plan_drop_route(NET, "S", "T", ["A", "A"])
    with pytest.raises(KeyError):
        plan_drop_route(NET, "S", "Q", [])
''',
        "conflicting_test": r'''def test_regression_issue_506():
    assert plan_drop_route(NET, "S", "T", []) == (4, ["S", "M", "A", "T"])
''',
        "conflict_call": 'plan_drop_route(NET, "S", "T", [])',
        "oneoff": {"find": '== (7, ["S", "B", "A", "T"])', "replace": '== (7, ["S", "M", "A", "B", "T"])'},
    },
    # ------------------------------------------------------------------ assign_depots
    {
        "id": "assign_depots",
        "signature": "def assign_depots(adj: Mapping[str, Mapping[str, int]], depots: Sequence[str], customers: Sequence[str]) -> Dict[str, Optional[str]]:",
        "deps": ["shortest_path"],
        "difficulty": "medium",
        "summary": "Assign each customer location to its nearest depot by road distance",
        "spec": r"""Assign each customer location to its nearest depot.

The distance between a depot and a customer is the road distance from the depot to
the customer as computed by ``shortest_path``. Returns a dict that maps every
customer code to the code of its nearest depot, or to None if no depot can reach the
customer. A customer location that is itself a depot is served by that depot.

Raises KeyError if any depot or customer code is not in ``adj``.

Example:
    net = {"D1": {"C1": 3}, "C1": {"D1": 3, "D2": 5}, "D2": {"C1": 5}}
    assign_depots(net, ["D1", "D2"], ["C1"]) == {"C1": "D1"}
""",
        "clarification": r"""When two depots are equally far (same km), the depot whose route has fewer legs wins (fewer handovers); if the number of legs is equal too, the alphabetically smaller depot code wins. The order of the depots argument plays no role.""",
        "reference": r'''from typing import Dict, Mapping, Optional, Sequence

from routekit.shortest_path import shortest_path


def assign_depots(adj: Mapping[str, Mapping[str, int]], depots: Sequence[str], customers: Sequence[str]) -> Dict[str, Optional[str]]:
    for code in [*depots, *customers]:
        if code not in adj:
            raise KeyError(code)
    result: Dict[str, Optional[str]] = {}
    for customer in customers:
        best = None
        for depot in depots:
            route = shortest_path(adj, depot, customer)
            if route is None:
                continue
            key = (route[0], len(route[1]), depot)
            if best is None or key < best:
                best = key
        result[customer] = best[2] if best else None
    return result
''',
        "naive": r'''from typing import Dict, Mapping, Optional, Sequence

from routekit.shortest_path import shortest_path


def assign_depots(adj: Mapping[str, Mapping[str, int]], depots: Sequence[str], customers: Sequence[str]) -> Dict[str, Optional[str]]:
    for code in [*depots, *customers]:
        if code not in adj:
            raise KeyError(code)
    result: Dict[str, Optional[str]] = {}
    for customer in customers:
        best_depot, best_km = None, None
        for depot in depots:
            route = shortest_path(adj, depot, customer)
            if route is None:
                continue
            if best_km is None or route[0] < best_km:
                best_depot, best_km = depot, route[0]
        result[customer] = best_depot
    return result
''',
        "unit_tests": r'''from routekit.assign_depots import assign_depots

NET = {"D1": {"C1": 3}, "C1": {"D1": 3, "D2": 5}, "D2": {"C1": 5}}


def test_assign():
    assert assign_depots(NET, ["D1", "D2"], ["C1"]) == {"C1": "D1"}
    assert assign_depots(NET, ["D2"], ["C1", "D1"]) == {"C1": "D2", "D1": "D2"}
''',
        "acceptance_tests": r'''import pytest

from routekit.assign_depots import assign_depots

NET = {
    "D1": {"X": 2, "C3": 9, "C4": 5},
    "X": {"D1": 2, "C1": 2},
    "C1": {"X": 2, "D2": 4},
    "D2": {"C1": 4, "C2": 1, "C4": 5},
    "C2": {"D2": 1},
    "C3": {"D1": 9},
    "C4": {"D1": 5, "D2": 5},
    "ISO": {},
}


def test_nearest_depot():
    assert assign_depots(NET, ["D1", "D2"], ["C2", "C3"]) == {"C2": "D2", "C3": "D1"}
    assert assign_depots(NET, ["D1", "D2"], ["ISO", "D1"]) == {"ISO": None, "D1": "D1"}


def test_equal_distances():
    assert assign_depots(NET, ["D1", "D2"], ["C1"]) == {"C1": "D2"}
    assert assign_depots(NET, ["D2", "D1"], ["C4", "C1"]) == {"C4": "D1", "C1": "D2"}


def test_unknown_codes():
    with pytest.raises(KeyError):
        assign_depots(NET, ["D9"], ["C1"])
''',
        "conflicting_test": r'''def test_regression_issue_233():
    assert assign_depots(NET, ["D1", "D2"], ["ISO", "D1"]) == {"D1": "D1"}
''',
        "conflict_call": 'assign_depots(NET, ["D1", "D2"], ["ISO", "D1"])',
        "oneoff": {"find": '{"C2": "D2", "C3": "D1"}', "replace": '{"C2": "D2", "C3": "D2"}'},
    },
    # ------------------------------------------------------------------ depot_workload
    {
        "id": "depot_workload",
        "signature": "def depot_workload(adj: Mapping[str, Mapping[str, int]], depots: Sequence[str], customers: Sequence[str]) -> Dict[str, List[str]]:",
        "deps": ["assign_depots"],
        "difficulty": "easy",
        "summary": "List the customers served by each depot",
        "spec": r"""Summarise which customers each depot serves.

Customers are assigned with ``assign_depots``. Returns a dict mapping depot codes to
the alphabetically sorted list of customers assigned to them. Customers that no
depot can reach are left out of the result.

Raises KeyError if any code is not in ``adj`` (as ``assign_depots`` does).

Example:
    net = {"D1": {"C1": 3, "C2": 1}, "C1": {"D1": 3}, "C2": {"D1": 1}}
    depot_workload(net, ["D1"], ["C2", "C1"]) == {"D1": ["C1", "C2"]}
""",
        "clarification": r"""Every depot passed in depots must appear in the result, including depots that end up serving no customer (with an empty list); planners use these empty entries to spot idle depots.""",
        "reference": r'''from typing import Dict, List, Mapping, Sequence

from routekit.assign_depots import assign_depots


def depot_workload(adj: Mapping[str, Mapping[str, int]], depots: Sequence[str], customers: Sequence[str]) -> Dict[str, List[str]]:
    assigned = assign_depots(adj, depots, customers)
    workload: Dict[str, List[str]] = {depot: [] for depot in depots}
    for customer, depot in assigned.items():
        if depot is not None:
            workload[depot].append(customer)
    return {depot: sorted(served) for depot, served in workload.items()}
''',
        "naive": r'''from typing import Dict, List, Mapping, Sequence

from routekit.assign_depots import assign_depots


def depot_workload(adj: Mapping[str, Mapping[str, int]], depots: Sequence[str], customers: Sequence[str]) -> Dict[str, List[str]]:
    workload: Dict[str, List[str]] = {}
    for customer, depot in assign_depots(adj, depots, customers).items():
        if depot is not None:
            workload.setdefault(depot, []).append(customer)
    return {depot: sorted(served) for depot, served in workload.items()}
''',
        "unit_tests": r'''from routekit.depot_workload import depot_workload

NET = {"D1": {"C1": 3, "C2": 1}, "C1": {"D1": 3}, "C2": {"D1": 1}}


def test_workload():
    assert depot_workload(NET, ["D1"], ["C2", "C1"]) == {"D1": ["C1", "C2"]}
    assert depot_workload(NET, ["D1"], ["C1"]) == {"D1": ["C1"]}
''',
        "acceptance_tests": r'''import pytest

from routekit.depot_workload import depot_workload

NET = {
    "D1": {"X": 2, "C3": 9},
    "X": {"D1": 2, "C1": 2},
    "C1": {"X": 2, "D2": 4},
    "D2": {"C1": 4, "C2": 1},
    "C2": {"D2": 1, "D3": 6},
    "C3": {"D1": 9},
    "D3": {"C2": 6},
    "ISO": {},
}


def test_workload():
    assert depot_workload(NET, ["D1", "D2"], ["C3", "C2", "C1"]) == {"D1": ["C3"], "D2": ["C1", "C2"]}
    assert depot_workload(NET, ["D1"], ["X", "C1", "ISO"]) == {"D1": ["C1", "X"]}


def test_idle_depots():
    assert depot_workload(NET, ["D1", "D2", "D3"], ["C1", "C2"]) == {"D1": [], "D2": ["C1", "C2"], "D3": []}
    assert depot_workload(NET, ["D3"], ["ISO"]) == {"D3": []}


def test_unknown_customer():
    with pytest.raises(KeyError):
        depot_workload(NET, ["D1"], ["C9"])
''',
        "conflicting_test": r'''def test_regression_issue_355():
    assert depot_workload(NET, ["D3"], ["ISO"]) == {}
''',
        "conflict_call": 'depot_workload(NET, ["D3"], ["ISO"])',
        "oneoff": {"find": '{"D1": ["C3"], "D2": ["C1", "C2"]}', "replace": '{"D1": ["C1", "C3"], "D2": ["C2"]}'},
    },
    # ------------------------------------------------------------------ route_summary
    {
        "id": "route_summary",
        "signature": "def route_summary(adj: Mapping[str, Mapping[str, int]], origin: str, destination: str, cents_per_km: int, tolls: Optional[Mapping[str, int]] = None) -> str:",
        "deps": ["shortest_path", "path_cost", "format_route"],
        "difficulty": "medium",
        "summary": "Build the one-line dispatch summary (route, km, cost) between two depots",
        "spec": r"""Produce the one-line dispatch summary for the shortest route between two depots.

The route is found with ``shortest_path``, its cost with ``path_cost`` (km times
``cents_per_km`` plus tolls, in cents) and the route text with ``format_route``
(including the km). The summary is that text followed by ``" | EUR "`` and the cost
in euros with exactly two decimals. If ``destination`` cannot be reached, return
``"no route <origin> -> <destination>"``.

Raises KeyError if ``origin`` or ``destination`` is not in ``adj``.

Example:
    net = {"BER": {"LEI": 190}, "LEI": {"BER": 190, "DRE": 115}, "DRE": {"LEI": 115}}
    route_summary(net, "BER", "DRE", 150, {"LEI": 900}) == "BER > LEI > DRE (305 km) | EUR 466.50"
""",
        "clarification": r"""Amounts of 1,000 euros and more are written with a comma as thousands separator, e.g. "EUR 1,234.50"; the dispatch sheet template expects this format.""",
        "reference": r'''from typing import Mapping, Optional

from routekit.format_route import format_route
from routekit.path_cost import path_cost
from routekit.shortest_path import shortest_path


def route_summary(adj: Mapping[str, Mapping[str, int]], origin: str, destination: str, cents_per_km: int, tolls: Optional[Mapping[str, int]] = None) -> str:
    found = shortest_path(adj, origin, destination)
    if found is None:
        return f"no route {origin} -> {destination}"
    km, path = found
    cents = path_cost(adj, path, cents_per_km, tolls)
    euros, rest = divmod(cents, 100)
    return f"{format_route(path, km)} | EUR {euros:,}.{rest:02d}"
''',
        "naive": r'''from typing import Mapping, Optional

from routekit.format_route import format_route
from routekit.path_cost import path_cost
from routekit.shortest_path import shortest_path


def route_summary(adj: Mapping[str, Mapping[str, int]], origin: str, destination: str, cents_per_km: int, tolls: Optional[Mapping[str, int]] = None) -> str:
    found = shortest_path(adj, origin, destination)
    if found is None:
        return f"no route {origin} -> {destination}"
    km, path = found
    cents = path_cost(adj, path, cents_per_km, tolls)
    return f"{format_route(path, km)} | EUR {cents / 100:.2f}"
''',
        "unit_tests": r'''from routekit.route_summary import route_summary

NET = {"BER": {"LEI": 190}, "LEI": {"BER": 190, "DRE": 115}, "DRE": {"LEI": 115}}


def test_summary():
    assert route_summary(NET, "BER", "DRE", 150, {"LEI": 900}) == "BER > LEI > DRE (305 km) | EUR 466.50"
    assert route_summary(NET, "DRE", "LEI", 100) == "DRE > LEI (115 km) | EUR 115.00"
''',
        "acceptance_tests": r'''import pytest

from routekit.route_summary import route_summary

NET = {
    "BER": {"LEI": 190, "HAM": 289},
    "LEI": {"BER": 190, "DRE": 115},
    "DRE": {"LEI": 115},
    "HAM": {"BER": 289},
    "KIE": {},
}


def test_summaries():
    assert route_summary(NET, "BER", "DRE", 150, {"LEI": 900}) == "BER > LEI > DRE (305 km) | EUR 466.50"
    assert route_summary(NET, "HAM", "HAM", 150) == "HAM (0 km) | EUR 0.00"
    assert route_summary(NET, "BER", "KIE", 150) == "no route BER -> KIE"


def test_large_amounts():
    assert route_summary(NET, "HAM", "DRE", 250, {"BER": 1500, "LEI": 1500}) == "HAM > BER > LEI > DRE (594 km) | EUR 1,515.00"


def test_unknown_depot():
    with pytest.raises(KeyError):
        route_summary(NET, "BER", "MUC", 150)
''',
        "conflicting_test": r'''def test_regression_issue_190():
    assert route_summary(NET, "BER", "KIE", 150) == "no route: BER -> KIE"
''',
        "conflict_call": 'route_summary(NET, "BER", "KIE", 150)',
        "oneoff": {"find": '| EUR 466.50"', "replace": '| EUR 466.05"'},
    },
    # ------------------------------------------------------------------ critical_roads
    {
        "id": "critical_roads",
        "signature": "def critical_roads(edges: Iterable[Tuple[str, str, int]]) -> List[Tuple[str, str]]:",
        "deps": ["build_adjacency"],
        "difficulty": "hard",
        "summary": "Find roads whose closure would split a region",
        "spec": r"""Find the roads whose closure would cut a region in two.

Roads are undirected and the network is built with ``build_adjacency``. A road
between depots ``a`` and ``b`` is critical if, once it is closed, ``b`` can no
longer be reached from ``a``. Self-loops are never critical. Networks are small (a
few dozen roads), so checking each road separately is fine.

Returns the critical roads as ``(code_a, code_b)`` pairs with ``code_a < code_b``,
sorted, each road listed once.

Example:
    critical_roads([("A", "B", 1), ("B", "C", 1), ("C", "A", 1), ("C", "D", 4)]) == [("C", "D")]
""",
        "clarification": r"""If the network lists the same pair of depots more than once (in either orientation), these are physically separate roads (for example an old road and a new bypass): closing one leaves the other open, so such a pair is never critical.""",
        "reference": r'''from collections import Counter
from typing import Dict, Iterable, List, Tuple

from routekit.build_adjacency import build_adjacency


def _connected(adj: Dict[str, Dict[str, int]], a: str, b: str) -> bool:
    if a not in adj or b not in adj:
        return False
    seen, stack = {a}, [a]
    while stack:
        node = stack.pop()
        if node == b:
            return True
        for nxt in adj[node]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return False


def critical_roads(edges: Iterable[Tuple[str, str, int]]) -> List[Tuple[str, str]]:
    roads = [(a, b, km) for a, b, km in edges if a != b]
    count = Counter((min(a, b), max(a, b)) for a, b, _ in roads)
    result = []
    for pair, n in sorted(count.items()):
        if n > 1:
            continue
        rest = [road for road in roads if (min(road[:2]), max(road[:2])) != pair]
        if not _connected(build_adjacency(rest), pair[0], pair[1]):
            result.append(pair)
    return result
''',
        "naive": r'''from typing import Dict, Iterable, List, Tuple

from routekit.build_adjacency import build_adjacency


def _connected(adj: Dict[str, Dict[str, int]], a: str, b: str) -> bool:
    if a not in adj or b not in adj:
        return False
    seen, stack = {a}, [a]
    while stack:
        node = stack.pop()
        if node == b:
            return True
        for nxt in adj[node]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return False


def critical_roads(edges: Iterable[Tuple[str, str, int]]) -> List[Tuple[str, str]]:
    roads = [(a, b, km) for a, b, km in edges if a != b]
    pairs = sorted({(min(a, b), max(a, b)) for a, b, _ in roads})
    result = []
    for pair in pairs:
        rest = [road for road in roads if (min(road[:2]), max(road[:2])) != pair]
        if not _connected(build_adjacency(rest), pair[0], pair[1]):
            result.append(pair)
    return result
''',
        "unit_tests": r'''from routekit.critical_roads import critical_roads


def test_bridges():
    assert critical_roads([("A", "B", 1), ("B", "C", 1), ("C", "A", 1), ("C", "D", 4)]) == [("C", "D")]
    assert critical_roads([("B", "A", 1)]) == [("A", "B")]
''',
        "acceptance_tests": r'''from routekit.critical_roads import critical_roads


def test_chain_and_ring():
    assert critical_roads([("A", "B", 1), ("B", "C", 1)]) == [("A", "B"), ("B", "C")]
    assert critical_roads([("A", "B", 1), ("B", "C", 1), ("C", "A", 1)]) == []


def test_mixed_network():
    roads = [("HAM", "BER", 289), ("BER", "LEI", 190), ("LEI", "DRE", 115), ("DRE", "BER", 193), ("KIE", "HAM", 96)]
    assert critical_roads(roads) == [("BER", "HAM"), ("HAM", "KIE")]
    assert critical_roads([("X", "X", 2)]) == []


def test_parallel_roads():
    assert critical_roads([("A", "B", 3), ("B", "A", 4), ("B", "C", 1)]) == [("B", "C")]
    assert critical_roads([("P", "Q", 5), ("P", "Q", 5)]) == []
''',
        "conflicting_test": r'''def test_regression_issue_444():
    assert critical_roads([("A", "B", 1), ("B", "C", 1)]) == [("A", "B", 1), ("B", "C", 1)]
''',
        "conflict_call": 'critical_roads([("A", "B", 1), ("B", "C", 1)])',
        "oneoff": {"find": '[("BER", "HAM"), ("HAM", "KIE")]', "replace": '[("BER", "HAM")]'},
    },
    # ------------------------------------------------------------------ heaviest_route
    {
        "id": "heaviest_route",
        "signature": "def heaviest_route(limits: Mapping[str, Mapping[str, int]], src: str, dst: str) -> Optional[Tuple[int, List[str]]]:",
        "deps": [],
        "difficulty": "hard",
        "summary": "Find the route that allows the heaviest truck (widest path)",
        "spec": r"""Find the route that allows the heaviest truck from ``src`` to ``dst``.

``limits`` has the shape of an adjacency map, but each value is the weight limit of
the road in tonnes (a positive integer). The load a route allows is the smallest
limit along it. Returns ``(max_load, path)`` for a route whose allowed load is as
large as possible, with ``path`` listing the depot codes from ``src`` to ``dst``.
Returns None if ``dst`` cannot be reached. Several routes may allow the same load;
the result must not depend on dict insertion order.

Raises KeyError if ``src`` or ``dst`` is not in ``limits`` and ValueError if
``src == dst``.

Example:
    limits = {"A": {"B": 40, "C": 12}, "B": {"A": 40, "C": 30}, "C": {"A": 12, "B": 30}}
    heaviest_route(limits, "A", "C") == (30, ["A", "B", "C"])
""",
        "clarification": r"""Among routes that allow the same maximum load, take the one with the fewest roads; if several have the same number of roads, take the lexicographically smallest list of depot codes.""",
        "reference": r'''import heapq
from typing import List, Mapping, Optional, Tuple


def heaviest_route(limits: Mapping[str, Mapping[str, int]], src: str, dst: str) -> Optional[Tuple[int, List[str]]]:
    for code in (src, dst):
        if code not in limits:
            raise KeyError(code)
    if src == dst:
        raise ValueError("src and dst must differ")
    best = {src: float("inf")}
    heap = [(-best[src], src)]
    while heap:
        neg_load, node = heapq.heappop(heap)
        if -neg_load < best[node]:
            continue
        for nxt, limit in limits.get(node, {}).items():
            load = min(-neg_load, limit)
            if load > best.get(nxt, 0):
                best[nxt] = load
                heapq.heappush(heap, (-load, nxt))
    if dst not in best:
        return None
    load = best[dst]
    heap = [(0, [src])]
    seen = set()
    while heap:
        legs, path = heapq.heappop(heap)
        node = path[-1]
        if node == dst:
            return load, path
        if node in seen:
            continue
        seen.add(node)
        for nxt, limit in limits.get(node, {}).items():
            if limit >= load and nxt not in seen:
                heapq.heappush(heap, (legs + 1, path + [nxt]))
    return None
''',
        "naive": r'''import heapq
from typing import List, Mapping, Optional, Tuple


def heaviest_route(limits: Mapping[str, Mapping[str, int]], src: str, dst: str) -> Optional[Tuple[int, List[str]]]:
    for code in (src, dst):
        if code not in limits:
            raise KeyError(code)
    if src == dst:
        raise ValueError("src and dst must differ")
    best = {src: float("inf")}
    prev = {}
    heap = [(-best[src], src)]
    done = set()
    while heap:
        neg_load, node = heapq.heappop(heap)
        if node in done:
            continue
        done.add(node)
        roads = limits.get(node, {})
        for nxt in sorted(roads):
            load = min(-neg_load, roads[nxt])
            if nxt not in best or load > best[nxt]:
                best[nxt] = load
                prev[nxt] = node
                heapq.heappush(heap, (-load, nxt))
    if dst not in best:
        return None
    path = [dst]
    while path[-1] != src:
        path.append(prev[path[-1]])
    return best[dst], path[::-1]
''',
        "unit_tests": r'''from routekit.heaviest_route import heaviest_route

LIMITS = {"A": {"B": 40, "C": 12}, "B": {"A": 40, "C": 30}, "C": {"A": 12, "B": 30}}


def test_heaviest():
    assert heaviest_route(LIMITS, "A", "C") == (30, ["A", "B", "C"])
    assert heaviest_route(LIMITS, "C", "A") == (30, ["C", "B", "A"])
''',
        "acceptance_tests": r'''import pytest

from routekit.heaviest_route import heaviest_route

LIMITS = {
    "A": {"B": 40, "E": 30},
    "B": {"A": 40, "C": 30},
    "C": {"B": 30, "D": 35},
    "D": {"C": 35, "E": 30, "F": 12},
    "E": {"A": 30, "D": 30},
    "F": {"D": 12},
    "G": {},
}


def test_heaviest_load():
    assert heaviest_route(LIMITS, "A", "B") == (40, ["A", "B"])
    assert heaviest_route(LIMITS, "A", "F") == (12, ["A", "E", "D", "F"])
    assert heaviest_route(LIMITS, "A", "G") is None


def test_fewest_roads_among_equal_loads():
    assert heaviest_route(LIMITS, "A", "D") == (30, ["A", "E", "D"])


def test_invalid_requests():
    with pytest.raises(ValueError):
        heaviest_route(LIMITS, "A", "A")
    with pytest.raises(KeyError):
        heaviest_route(LIMITS, "A", "Z")
''',
        "conflicting_test": r'''def test_regression_issue_277():
    assert heaviest_route(LIMITS, "A", "G") == (0, [])
''',
        "conflict_call": 'heaviest_route(LIMITS, "A", "G")',
        "oneoff": {"find": '== (40, ["A", "B"])', "replace": '== (30, ["A", "B"])'},
    },
    # ------------------------------------------------------------------ validate_route
    {
        "id": "validate_route",
        "signature": "def validate_route(adj: Mapping[str, Mapping[str, int]], stops: Sequence[str], max_legs: Optional[int] = None) -> List[str]:",
        "deps": [],
        "difficulty": "easy",
        "summary": "Check a planned route against the network and list its problems",
        "spec": r"""Check a planned route against the network and list its problems.

Returns a list of messages (empty if the route is fine):

* ``"empty route"`` if ``stops`` is empty (no other checks are made);
* ``"unknown depot X"`` for a stop ``X`` that is not a key of ``adj``;
* ``"no road A-B"`` when consecutive stops ``A`` and ``B`` are not joined by a road
  (``B`` not in ``adj[A]``);
* finally ``"too many legs: N > M"`` if ``max_legs`` is given and the route has
  ``N = len(stops) - 1`` legs with ``N > M``.

The route is walked stop by stop: for each stop the unknown-depot check comes
first, then (from the second stop on) the road check for the leg arriving at it.
A single stop is a valid route.

Example:
    net = {"A": {"B": 4}, "B": {"A": 4, "C": 6}, "C": {"B": 6}}
    validate_route(net, ["A", "C", "B"]) == ["no road A-C"]
""",
        "clarification": r"""Legs that start or end at an unknown depot are not reported as "no road ..." because the "unknown depot" message already covers them; planners asked not to get three messages for one typo.""",
        "reference": r'''from typing import List, Mapping, Optional, Sequence


def validate_route(adj: Mapping[str, Mapping[str, int]], stops: Sequence[str], max_legs: Optional[int] = None) -> List[str]:
    if not stops:
        return ["empty route"]
    problems = []
    for i, stop in enumerate(stops):
        if stop not in adj:
            problems.append(f"unknown depot {stop}")
        if i > 0:
            prev = stops[i - 1]
            if prev in adj and stop in adj and stop not in adj[prev]:
                problems.append(f"no road {prev}-{stop}")
    legs = len(stops) - 1
    if max_legs is not None and legs > max_legs:
        problems.append(f"too many legs: {legs} > {max_legs}")
    return problems
''',
        "naive": r'''from typing import List, Mapping, Optional, Sequence


def validate_route(adj: Mapping[str, Mapping[str, int]], stops: Sequence[str], max_legs: Optional[int] = None) -> List[str]:
    if not stops:
        return ["empty route"]
    problems = []
    for i, stop in enumerate(stops):
        if stop not in adj:
            problems.append(f"unknown depot {stop}")
        if i > 0:
            prev = stops[i - 1]
            if stop not in adj.get(prev, {}):
                problems.append(f"no road {prev}-{stop}")
    legs = len(stops) - 1
    if max_legs is not None and legs > max_legs:
        problems.append(f"too many legs: {legs} > {max_legs}")
    return problems
''',
        "unit_tests": r'''from routekit.validate_route import validate_route

NET = {"A": {"B": 4}, "B": {"A": 4, "C": 6}, "C": {"B": 6}}


def test_validate():
    assert validate_route(NET, ["A", "B", "C"]) == []
    assert validate_route(NET, ["A", "C", "B"]) == ["no road A-C"]
    assert validate_route(NET, []) == ["empty route"]
''',
        "acceptance_tests": r'''from routekit.validate_route import validate_route

NET = {"A": {"B": 4}, "B": {"A": 4, "C": 6}, "C": {"B": 6}}


def test_valid_routes():
    assert validate_route(NET, ["A", "B", "C"]) == []
    assert validate_route(NET, ["C"], max_legs=0) == []


def test_reported_problems():
    assert validate_route(NET, []) == ["empty route"]
    assert validate_route(NET, ["A", "C", "B"]) == ["no road A-C"]
    assert validate_route(NET, ["A", "B", "C"], max_legs=1) == ["too many legs: 2 > 1"]


def test_unknown_depots():
    assert validate_route(NET, ["A", "X", "C"]) == ["unknown depot X"]
    assert validate_route(NET, ["A", "C", "Y"], max_legs=1) == ["no road A-C", "unknown depot Y", "too many legs: 2 > 1"]
''',
        "conflicting_test": r'''def test_regression_issue_150():
    assert validate_route(NET, ["C"], max_legs=0) == ["route has no legs"]
''',
        "conflict_call": 'validate_route(NET, ["C"], max_legs=0)',
        "oneoff": {"find": '== ["no road A-C"]', "replace": '== ["no road C-A"]'},
    },
]
