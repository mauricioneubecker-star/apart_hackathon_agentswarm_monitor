from typing import Sequence

from metricore.round_half_up import round_half_up


def apdex_score(latencies_ms: Sequence[float], target_ms: float) -> float:
    if not latencies_ms:
        raise ValueError("no latencies given")
    if target_ms <= 0:
        raise ValueError("target_ms must be positive")
    satisfied = tolerating = 0
    for v in latencies_ms:
        if v < target_ms:
            satisfied += 1
        elif v < 4 * target_ms:
            tolerating += 1
    return round_half_up((satisfied + tolerating / 2) / len(latencies_ms), 2)
