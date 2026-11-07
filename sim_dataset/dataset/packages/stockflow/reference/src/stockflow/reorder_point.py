import math
from fractions import Fraction

from stockflow.safety_stock import safety_stock

WINDOW_DAYS = 28


def reorder_point(daily_demand, lead_times, review_period_days: int = 0) -> int:
    if review_period_days < 0:
        raise ValueError("review_period_days must be >= 0")
    demand = list(daily_demand)[-WINDOW_DAYS:]
    leads = list(lead_times)
    buffer = safety_stock(demand, leads)
    avg_demand = Fraction(sum(demand), len(demand))
    avg_lead = Fraction(sum(leads), len(leads))
    return math.ceil(avg_demand * (avg_lead + review_period_days)) + buffer
