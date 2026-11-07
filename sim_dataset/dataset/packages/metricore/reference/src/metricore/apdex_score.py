from typing import Sequence

from metricore.round_half_up import round_half_up


def apdex_score(latencies_ms: Sequence[float], target_ms: float) -> float:
    if not latencies_ms:
        raise ValueError("no latencies given")
    if target_ms <= 0:
        raise ValueError("target_ms must be positive")
    satisfied = sum(1 for v in latencies_ms if v <= target_ms)
    tolerating = sum(1 for v in latencies_ms if target_ms < v <= 4 * target_ms)
    return round_half_up((satisfied + tolerating / 2) / len(latencies_ms), 2)
