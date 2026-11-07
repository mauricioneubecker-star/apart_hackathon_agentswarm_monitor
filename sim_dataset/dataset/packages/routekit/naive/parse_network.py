from typing import List, Tuple

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
