def select_lots_fefo(lots, qty, today, min_shelf_days=0):
    if qty < 0:
        raise ValueError("qty must be >= 0")
    eligible = [
        lot for lot in lots
        if lot[1] > today and lot[1] - today >= min_shelf_days and lot[2] > 0
    ]
    eligible.sort(key=lambda lot: (lot[1], lot[0]))
    picks = []
    remaining = qty
    for lot_id, _expiry, available in eligible:
        if remaining == 0:
            break
        take = min(available, remaining)
        picks.append((lot_id, take))
        remaining -= take
    if remaining > 0:
        raise ValueError("not enough eligible stock")
    return picks
