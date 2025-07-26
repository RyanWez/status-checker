"""
Timezone utilities for Myanmar timezone conversion
"""
from datetime import datetime, timezone, timedelta

# Myanmar timezone (UTC+6:30)
MYANMAR_TZ = timezone(timedelta(hours=6, minutes=30))

def to_myanmar_time(dt: datetime) -> datetime:
    """Convert datetime to Myanmar timezone"""
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(MYANMAR_TZ)

def myanmar_now() -> datetime:
    """Get current time in Myanmar timezone"""
    return datetime.now(MYANMAR_TZ)

def format_myanmar_time(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format datetime in Myanmar timezone"""
    if dt is None:
        return "Never"
    
    myanmar_dt = to_myanmar_time(dt)
    return myanmar_dt.strftime(format_str)

def format_myanmar_time_short(dt: datetime) -> str:
    """Format datetime in Myanmar timezone (short format)"""
    return format_myanmar_time(dt, '%H:%M:%S')

def format_myanmar_date(dt: datetime) -> str:
    """Format date in Myanmar timezone"""
    return format_myanmar_time(dt, '%Y-%m-%d %H:%M')