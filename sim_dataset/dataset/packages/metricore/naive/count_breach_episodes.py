from typing import Optional, Sequence


def count_breach_episodes(samples: Sequence[Optional[float]], threshold: float,
                          min_duration: int = 1) -> int:
    if min_duration < 1:
        raise ValueError("min_duration must be >= 1")
    episodes = 0
    run = 0
    for sample in list(samples) + [None]:
        if sample is not None and sample > threshold:
            run += 1
        else:
            if run >= min_duration:
                episodes += 1
            run = 0
    return episodes
