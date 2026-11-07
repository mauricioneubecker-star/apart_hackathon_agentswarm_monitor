from typing import Dict, Optional, Sequence

from metricore.percentile import percentile
from metricore.round_half_up import round_half_up


def latency_summary(latencies_ms: Sequence[float]) -> Dict[str, Optional[float]]:
    if not latencies_ms:
        return {"count": 0, "min": None, "mean": None, "p50": None,
                "p95": None, "p99": None, "max": None}
    return {
        "count": len(latencies_ms),
        "min": round_half_up(min(latencies_ms), 1),
        "mean": round_half_up(sum(latencies_ms) / len(latencies_ms), 1),
        "p50": round_half_up(percentile(latencies_ms, 50), 1),
        "p95": round_half_up(percentile(latencies_ms, 95), 1),
        "p99": round_half_up(percentile(latencies_ms, 99), 1),
        "max": round_half_up(max(latencies_ms), 1),
    }
