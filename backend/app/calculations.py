"""Pure calculation functions - no database dependencies."""
from datetime import time, timedelta


def compute_sleep(bedtime: time, waketime: time) -> float:
    """Calculate sleep duration in hours, minus 1h fall-asleep time."""
    bed = timedelta(hours=bedtime.hour, minutes=bedtime.minute)
    wake = timedelta(hours=waketime.hour, minutes=waketime.minute)
    if wake < bed:
        wake += timedelta(days=1)
    duration = (wake - bed - timedelta(hours=1)).total_seconds() / 3600
    return max(0, duration)


def compute_fasting(breakfast: time, dinner: time) -> float:
    """Calculate fasting duration (dinner to next breakfast)."""
    brk = timedelta(hours=breakfast.hour, minutes=breakfast.minute)
    din = timedelta(hours=dinner.hour, minutes=dinner.minute)
    if brk > din:
        fasting = brk - din
    else:
        fasting = timedelta(hours=24) - (din - brk)
    return fasting.total_seconds() / 3600
