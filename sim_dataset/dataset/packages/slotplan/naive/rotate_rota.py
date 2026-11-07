from typing import List, Sequence


def rotate_rota(staff: Sequence[str], n_days: int, per_day: int, first_day: int = 0) -> List[List[str]]:
    people = list(staff)
    if not people or per_day < 1 or per_day > len(people):
        raise ValueError("per_day must be between 1 and the number of staff")
    if n_days < 0 or not 0 <= first_day <= 6:
        raise ValueError("invalid n_days or first_day")
    rota: List[List[str]] = []
    position = 0
    for _ in range(n_days):
        rota.append([people[(position + k) % len(people)] for k in range(per_day)])
        position = (position + per_day) % len(people)
    return rota
