import math
from fractions import Fraction


def safety_stock(daily_demand, lead_times) -> int:
    demand = list(daily_demand)
    leads = list(lead_times)
    if not demand or not leads:
        raise ValueError("demand history and lead times are required")
    if min(demand) < 0 or min(leads) < 0:
        raise ValueError("negative demand or lead time")
    average_part = Fraction(sum(demand) * sum(leads), len(demand) * len(leads))
    value = max(demand) * max(leads) - average_part
    return max(0, math.ceil(value))
