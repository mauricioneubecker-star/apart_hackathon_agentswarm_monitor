from typing import Dict, List, Mapping, Sequence

from routekit.assign_depots import assign_depots


def depot_workload(adj: Mapping[str, Mapping[str, int]], depots: Sequence[str], customers: Sequence[str]) -> Dict[str, List[str]]:
    assigned = assign_depots(adj, depots, customers)
    workload: Dict[str, List[str]] = {depot: [] for depot in depots}
    for customer, depot in assigned.items():
        if depot is not None:
            workload[depot].append(customer)
    return {depot: sorted(served) for depot, served in workload.items()}
