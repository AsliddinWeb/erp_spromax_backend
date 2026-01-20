from datetime import datetime, timedelta
from typing import Optional
import pytz


def get_current_utc() -> datetime:
    """Joriy UTC vaqtni olish"""
    return datetime.utcnow()


def get_current_uzbekistan_time() -> datetime:
    """Joriy O'zbekiston vaqtini olish"""
    uzbekistan_tz = pytz.timezone('Asia/Tashkent')
    return datetime.now(uzbekistan_tz)


def convert_to_uzbekistan_time(dt: datetime) -> datetime:
    """UTC vaqtni O'zbekiston vaqtiga o'tkazish"""
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    uzbekistan_tz = pytz.timezone('Asia/Tashkent')
    return dt.astimezone(uzbekistan_tz)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Datetime'ni format qilish"""
    return dt.strftime(format_str)


def add_days(dt: datetime, days: int) -> datetime:
    """Sanaga kunlar qo'shish"""
    return dt + timedelta(days=days)


def add_hours(dt: datetime, hours: int) -> datetime:
    """Vaqtga soatlar qo'shish"""
    return dt + timedelta(hours=hours)


def get_date_range(start_date: datetime, end_date: datetime) -> int:
    """Ikki sana orasidagi kunlar sonini hisoblash"""
    return (end_date - start_date).days