def first_fit_decreasing(items, capacity):
    if capacity <= 0:
        raise ValueError("capacity must be positive")
    for _item_id, weight in items:
        if weight < 0 or weight > capacity:
            raise ValueError(f"item weight out of range: {weight}")
    ordered = sorted((tuple(item) for item in items), key=lambda item: item[1], reverse=True)
    bins = []
    free = []
    for item in ordered:
        for i, room in enumerate(free):
            if item[1] <= room:
                bins[i].append(item)
                free[i] -= item[1]
                break
        else:
            bins.append([item])
            free.append(capacity - item[1])
    return bins
