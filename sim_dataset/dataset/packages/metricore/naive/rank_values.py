from typing import List, Sequence


def rank_values(values: Sequence[float]) -> List[int]:
    distinct = sorted(set(values), reverse=True)
    rank_of = {value: rank for rank, value in enumerate(distinct, start=1)}
    return [rank_of[value] for value in values]
