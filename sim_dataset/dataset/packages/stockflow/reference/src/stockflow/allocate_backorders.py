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
        if all(left.get(sku, 0) >= qty for sku, qty in lines.items()):
            for sku, qty in lines.items():
                left[sku] = left.get(sku, 0) - qty
            result[order_id] = dict(lines)
        else:
            result[order_id] = {sku: 0 for sku in lines}
    return result
