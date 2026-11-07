from typing import Any, Dict, Iterable, List, Mapping

from metricore.percentile import percentile
from metricore.round_half_up import round_half_up


def percentile_by_group(records: Iterable[Mapping[str, Any]], key: str, field: str,
                        p: float) -> Dict[Any, float]:
    if not 0 <= p <= 100:
        raise ValueError("p must be between 0 and 100")
    groups: Dict[Any, List[float]] = {}
    for record in records:
        if record.get(field) is None or record.get(key) is None:
            continue
        groups.setdefault(record[key], []).append(record[field])
    return {group: round_half_up(percentile(values, p), 1) for group, values in groups.items()}
