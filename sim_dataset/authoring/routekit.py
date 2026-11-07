"""Task package `routekit` (graph_routing). Function definitions live in _parts/routekit_{a,b,c}.py."""
import importlib.util
from pathlib import Path

_P = Path(__file__).resolve().parent / "_parts"


def _load(n):
    s = importlib.util.spec_from_file_location(f"_routekit_{n}", _P / f"routekit_{n}.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m.FUNCTIONS


PACKAGE = {
    "package_id": "routekit",
    "family": "graph_routing",
    "title": "routekit: road network and routing utilities for depot logistics",
    "description": (
        "Helpers used by the dispatch and network-planning teams to work with the depot road "
        "network: reading network files, building adjacency maps, shortest and heaviest-load "
        "routes, regions, road closures, depot assignment and dispatch summaries. Depot codes are "
        "short alphanumeric strings such as BER or HAM, road lengths are whole kilometres and "
        "money amounts are integer cents. All functions are pure and operate on small in-memory networks."
    ),
    "functions": _load("a") + _load("b") + _load("c"),
}
