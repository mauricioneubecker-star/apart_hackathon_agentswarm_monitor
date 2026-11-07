from typing import Tuple


def intervals_overlap(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    a_start, a_end = a
    b_start, b_end = b
    if a_start > a_end or b_start > b_end:
        raise ValueError("interval starts after it ends")
    return a_start < b_end and b_start < a_end
