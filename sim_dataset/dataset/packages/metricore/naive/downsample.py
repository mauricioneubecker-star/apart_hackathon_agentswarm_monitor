from typing import Dict, List, Sequence, Tuple


def downsample(points: Sequence[Tuple[int, float]], bucket_seconds: int,
               agg: str = "mean") -> List[Tuple[int, float]]:
    if bucket_seconds < 1:
        raise ValueError("bucket_seconds must be >= 1")
    if agg not in ("mean", "max", "sum", "last"):
        raise ValueError(f"unknown aggregation: {agg!r}")
    if not points:
        return []
    ordered = sorted(points, key=lambda point: point[0])
    origin = ordered[0][0]
    buckets: Dict[int, List[float]] = {}
    for ts, value in ordered:
        start = origin + (ts - origin) // bucket_seconds * bucket_seconds
        buckets.setdefault(start, []).append(value)
    result = []
    for start in sorted(buckets):
        values = buckets[start]
        if agg == "mean":
            out = round(sum(values) / len(values), 2)
        elif agg == "max":
            out = max(values)
        elif agg == "sum":
            out = sum(values)
        else:
            out = values[-1]
        result.append((start, out))
    return result
