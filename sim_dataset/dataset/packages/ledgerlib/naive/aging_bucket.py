def aging_bucket(days_past_due: int) -> str:
    if days_past_due >= 90:
        return "90+"
    if days_past_due > 60:
        return "61-90"
    if days_past_due > 30:
        return "31-60"
    if days_past_due > 0:
        return "1-30"
    return "current"
