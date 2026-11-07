from typing import Dict, List, Sequence


def rank_values(values: Sequence[float]) -> List[int]:
    first_position: Dict[float, int] = {}
    for position, value in enumerate(sorted(values, reverse=True), start=1):
        first_position.setdefault(value, position)
    return [first_position[value] for value in values]
