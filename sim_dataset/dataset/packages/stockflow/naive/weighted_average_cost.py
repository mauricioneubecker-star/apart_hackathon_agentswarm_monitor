def weighted_average_cost(layers) -> int:
    total_qty = 0
    total_cost = 0
    for qty, unit_cost in layers:
        if qty < 0 or unit_cost < 0:
            raise ValueError("negative quantity or cost in cost layers")
        total_qty += qty
        total_cost += qty * unit_cost
    if total_qty == 0:
        raise ValueError("cost layers hold no stock")
    return round(total_cost / total_qty)
