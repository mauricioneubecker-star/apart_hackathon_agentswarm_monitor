def fifo_cogs(layers, qty):
    if qty < 0:
        raise ValueError("qty must be >= 0")
    ordered = sorted(layers, key=lambda layer: layer[0])
    if qty > 0 and not ordered:
        raise ValueError("no cost layers to ship from")
    cost = 0
    remaining = []
    to_ship = qty
    for day, layer_qty, unit_cost in ordered:
        take = min(layer_qty, to_ship)
        cost += take * unit_cost
        to_ship -= take
        if layer_qty - take > 0:
            remaining.append((day, layer_qty - take, unit_cost))
    return cost, remaining
