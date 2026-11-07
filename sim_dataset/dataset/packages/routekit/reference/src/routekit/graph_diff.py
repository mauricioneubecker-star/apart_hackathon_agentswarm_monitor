from typing import Dict, List, Sequence, Tuple

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
