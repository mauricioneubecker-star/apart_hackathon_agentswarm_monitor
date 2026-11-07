def allocate_freight(freight_cents, line_values):
    values = list(line_values)
    if freight_cents < 0 or any(v < 0 for v in values):
        raise ValueError("negative amounts are not allowed")
    total = sum(values)
    if total == 0:
        if freight_cents > 0:
            raise ValueError("no line value to allocate freight against")
        return [0] * len(values)
    shares = []
    order = []
    for i, value in enumerate(values):
        share, rest = divmod(freight_cents * value, total)
        shares.append(share)
        order.append((-rest, -value, i))
    leftover = freight_cents - sum(shares)
    for _rest, _value, i in sorted(order)[:leftover]:
        shares[i] += 1
    return shares
