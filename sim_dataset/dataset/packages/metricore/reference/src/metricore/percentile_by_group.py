from typing import Any, Dict, Iterable, List, Mapping

from metricore.percentile import percentile
from metricore.round_half_up import round_half_up


def percentile_by_group(records: Iterable[Mapping[str, Any]], key: str, field: str,
                        p: float) -> Dict[Any, float]:
    if not 0 <= p <= 100:
        raise ValueError("p must be between 0 and 100")
    groups: Dict[Any, List[float]] = {}
    for record in records:
        value = record.get(field)
        if value is None:
            continue
        group = record.get(key)
        if group is None:
            group = "unknown"
        groups.setdefault(group, []).append(value)
    return {group: round_half_up(percentile(values, p), 1) for group, values in groups.items()}
