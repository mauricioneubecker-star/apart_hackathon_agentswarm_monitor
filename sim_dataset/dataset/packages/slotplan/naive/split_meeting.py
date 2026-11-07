from typing import List, Tuple


def split_meeting(start: int, end: int, max_block: int, break_len: int = 0) -> List[Tuple[int, int]]:
    if end <= start or max_block <= 0 or break_len < 0:
        raise ValueError("invalid session or block settings")
    blocks: List[Tuple[int, int]] = []
    cursor = start
    while cursor < end:
        block_end = min(cursor + max_block, end)
        blocks.append((cursor, block_end))
        cursor = block_end + break_len
    return blocks
