from typing import Optional, Sequence


def count_breach_episodes(samples: Sequence[Optional[float]], threshold: float,
                          min_duration: int = 1) -> int:
    if min_duration < 1:
        raise ValueError("min_duration must be >= 1")
    episodes = 0
    run = 0
    for sample in samples:
        if sample is None:
            continue
        if sample > threshold:
            run += 1
            continue
        if run >= min_duration:
            episodes += 1
        run = 0
    if run >= min_duration:
        episodes += 1
    return episodes
