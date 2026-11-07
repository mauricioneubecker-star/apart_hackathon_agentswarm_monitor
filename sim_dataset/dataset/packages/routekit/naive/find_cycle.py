from typing import Dict, Iterable, List, Optional, Tuple

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
