from typing import Dict, Optional, Sequence

from metricore.percentile import percentile
from metricore.round_half_up import round_half_up


def latency_summary(latencies_ms: Sequence[float]) -> Dict[str, Optional[float]]:
    data = list(latencies_ms)
    summary: Dict[str, Optional[float]] = {"count": len(data)}
    summary["min"] = round_half_up(min(data), 1)
    summary["mean"] = round_half_up(sum(data) / len(data), 1)
    for p in (50, 95, 99):
        summary[f"p{p}"] = round_half_up(percentile(data, p), 1)
    summary["max"] = round_half_up(max(data), 1)
    return summary
