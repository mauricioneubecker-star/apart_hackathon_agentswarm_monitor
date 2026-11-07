import heapq
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
