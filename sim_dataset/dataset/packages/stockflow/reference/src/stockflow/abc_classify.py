def abc_classify(values, a_pct=80, b_pct=95):
    if not 0 < a_pct <= b_pct <= 100:
        raise ValueError("thresholds must satisfy 0 < a_pct <= b_pct <= 100")
    if any(v < 0 for v in values.values()):
        raise ValueError("values must be >= 0")
    total = sum(values.values())
    ranked = sorted(values.items(), key=lambda kv: (-kv[1], kv[0]))
    classes = {}
    running = 0
    for sku, value in ranked:
        if value == 0:
            classes[sku] = "C"
        elif running * 100 < a_pct * total:
            classes[sku] = "A"
        elif running * 100 < b_pct * total:
            classes[sku] = "B"
        else:
            classes[sku] = "C"
        running += value
    return classes
