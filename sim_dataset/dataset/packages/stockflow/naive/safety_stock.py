def safety_stock(daily_demand, lead_times) -> int:
    demand = list(daily_demand)
    leads = list(lead_times)
    if not demand or not leads:
        raise ValueError("demand history and lead times are required")
    if min(demand) < 0 or min(leads) < 0:
        raise ValueError("negative demand or lead time")
    avg_demand = sum(demand) / len(demand)
    avg_lead = sum(leads) / len(leads)
    return max(0, int(max(demand) * max(leads) - avg_demand * avg_lead))
