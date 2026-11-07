from typing import Dict, List, Sequence, Tuple


def downsample(points: Sequence[Tuple[int, float]], bucket_seconds: int,
               agg: str = "mean") -> List[Tuple[int, float]]:
    if bucket_seconds < 1:
        raise ValueError("bucket_seconds must be >= 1")
    if agg not in ("mean", "max", "sum", "last"):
        raise ValueError(f"unknown aggregation: {agg!r}")
    buckets: Dict[int, List[Tuple[int, float]]] = {}
    for ts, value in points:
        buckets.setdefault(ts - ts % bucket_seconds, []).append((ts, value))
    result: List[Tuple[int, float]] = []
    for start in sorted(buckets):
        members = buckets[start]
        values = [value for _, value in members]
        if agg == "mean":
            out = round(sum(values) / len(values), 2)
        elif agg == "max":
            out = max(values)
        elif agg == "sum":
            out = sum(values)
        else:
            out = max(members, key=lambda member: member[0])[1]
        result.append((start, out))
    return result
