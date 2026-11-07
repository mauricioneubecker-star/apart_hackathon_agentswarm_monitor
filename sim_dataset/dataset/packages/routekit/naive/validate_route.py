from typing import List, Mapping, Optional, Sequence


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
