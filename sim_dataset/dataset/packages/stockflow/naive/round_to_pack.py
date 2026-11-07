def round_to_pack(qty: int, pack_size: int, min_packs: int = 1) -> int:
    if qty < 0 or pack_size < 1 or min_packs < 0:
        raise ValueError("invalid quantity, pack size or minimum")
    packs = -(-qty // pack_size)
    return max(packs, min_packs) * pack_size
