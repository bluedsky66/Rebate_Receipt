import random
from datetime import datetime, timedelta

def generate_timestamp(mode: str, fixed_dt: datetime | None, range_start: datetime | None, range_end: datetime | None) -> datetime:
    if mode == "recent":
        # Past 7 days, gaussian distribution leaning to past 3 days
        now = datetime.now()
        days_ago = random.gauss(3, 2)
        days_ago = max(0, min(6, days_ago))
        dt = now - timedelta(days=days_ago)
        # Randomize hours
        dt = dt.replace(hour=random.randint(7, 21), minute=random.randint(0, 59), second=random.randint(0, 59))
        return dt

    elif mode == "fixed":
        if not fixed_dt:
            return datetime.now()
        return fixed_dt

    elif mode == "range":
        if not range_start or not range_end:
            return datetime.now()
        if range_start >= range_end:
            raise ValueError("起始时间必须早于结束时间")
        delta = range_end - range_start
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return range_start + timedelta(seconds=random_seconds)

    return datetime.now()
