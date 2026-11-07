from typing import Any, Dict, List, Optional, Sequence

from metricore.latency_summary import latency_summary
from metricore.percent_change import percent_change


def latency_regression(before_ms: Sequence[float], after_ms: Sequence[float],
                       tolerance_pct: float = 10.0) -> Dict[str, Any]:
    if tolerance_pct < 0:
        raise ValueError("tolerance_pct must be >= 0")
    if not before_ms or not after_ms:
        raise ValueError("both samples must be non-empty")
    before = latency_summary(before_ms)
    after = latency_summary(after_ms)
    changes: Dict[str, Optional[float]] = {}
    regressed: List[str] = []
    for name in ("p50", "p95", "p99"):
        change = percent_change(before[name], after[name])
        changes[name] = change
        if change is None:
            if after[name] > 0:
                regressed.append(name)
        elif change > tolerance_pct:
            regressed.append(name)
    return {"changes": changes, "regressed": regressed,
            "verdict": "regression" if regressed else "ok"}
