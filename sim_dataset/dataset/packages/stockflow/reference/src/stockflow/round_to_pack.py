def round_to_pack(qty: int, pack_size: int, min_packs: int = 1) -> int:
    if qty < 0 or pack_size < 1 or min_packs < 0:
        raise ValueError("invalid quantity, pack size or minimum")
    packs, rest = divmod(qty, pack_size)
    if 2 * rest >= pack_size:
        packs += 1
    return max(packs, min_packs) * pack_size
