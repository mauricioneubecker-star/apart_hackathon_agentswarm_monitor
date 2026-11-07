from typing import Dict, List, Mapping, Sequence

from routekit.assign_depots import assign_depots


def depot_workload(adj: Mapping[str, Mapping[str, int]], depots: Sequence[str], customers: Sequence[str]) -> Dict[str, List[str]]:
    workload: Dict[str, List[str]] = {}
    for customer, depot in assign_depots(adj, depots, customers).items():
        if depot is not None:
            workload.setdefault(depot, []).append(customer)
    return {depot: sorted(served) for depot, served in workload.items()}
