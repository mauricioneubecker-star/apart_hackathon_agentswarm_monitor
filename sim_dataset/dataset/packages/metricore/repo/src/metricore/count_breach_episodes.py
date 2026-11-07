from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def count_breach_episodes(samples: Sequence[Optional[float]], threshold: float, min_duration: int = 1) -> int:
    """
    Count breach episodes in a series of per-minute latency samples.

    A sample breaches the SLA when it is above `threshold`. An episode is a
    maximal run of consecutive breaching samples; it is only counted if it lasts
    at least `min_duration` samples, so single-minute spikes can be ignored by
    raising min_duration. Minutes for which the scraper had no data appear in
    `samples` as None.

    - min_duration must be >= 1, otherwise ValueError is raised.
    - An empty series has 0 episodes.

    Example:
        count_breach_episodes([100, 400, 450, 120, 500], 300) == 2
    """
    raise NotImplementedError
