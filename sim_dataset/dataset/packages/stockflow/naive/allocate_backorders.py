def allocate_backorders(orders, available):
    seen = set()
    for order_id, _priority, _day, lines in orders:
        if order_id in seen:
            raise ValueError(f"duplicate order id {order_id!r}")
        seen.add(order_id)
        if any(qty <= 0 for qty in lines.values()):
            raise ValueError("line quantities must be positive")
    left = dict(available)
    result = {}
    for order_id, _priority, _day, lines in sorted(orders, key=lambda o: (o[1], o[2], o[0])):
        alloc = {}
        for sku, qty in lines.items():
            take = min(qty, max(left.get(sku, 0), 0))
            left[sku] = left.get(sku, 0) - take
            alloc[sku] = take
        result[order_id] = alloc
    return result
