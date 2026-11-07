from metricore.round_half_up import round_half_up


def error_budget_remaining(slo_target: float, total_requests: int, failed_requests: int) -> float:
    if not 0 < slo_target < 1:
        raise ValueError("slo_target must be between 0 and 1 (exclusive)")
    if total_requests < 0 or failed_requests < 0 or failed_requests > total_requests:
        raise ValueError("invalid request counts")
    if total_requests == 0:
        return 100.0
    budget = (1 - slo_target) * total_requests
    return round_half_up((budget - failed_requests) / budget * 100, 1)
