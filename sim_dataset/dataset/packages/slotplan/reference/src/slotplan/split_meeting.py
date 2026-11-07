from typing import List, Tuple


def split_meeting(start: int, end: int, max_block: int, break_len: int = 0) -> List[Tuple[int, int]]:
    if end <= start or max_block <= 0 or break_len < 0:
        raise ValueError("invalid session or block settings")
    total = end - start
    count = 1
    while count * max_block + (count - 1) * break_len < total:
        count += 1
    work = total - (count - 1) * break_len
    base, extra = divmod(work, count)
    blocks: List[Tuple[int, int]] = []
    cursor = start
    for index in range(count):
        length = base + (1 if index < extra else 0)
        blocks.append((cursor, cursor + length))
        cursor += length + break_len
    return blocks
