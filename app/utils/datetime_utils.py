from datetime import datetime, timedelta
from typing import Optional
import pytz

# ──────────────────────────────────────────────────────────────────────────────
# Tizim vaqt zonasi — superadmin o'zgartira oladi (set_timezone orqali)
# Default: Asia/Tashkent (UTC+5)
# ──────────────────────────────────────────────────────────────────────────────
_timezone_name: str = "Asia/Tashkent"


def set_timezone(tz_name: str) -> None:
    """Tizim vaqt zonasini o'zgartirish (superadmin uchun)"""
    global _timezone_name
    pytz.timezone(tz_name)  # Noto'g'ri tz bo'lsa exception
    _timezone_name = tz_name


def get_timezone_name() -> str:
    """Joriy vaqt zonasi nomini olish"""
    return _timezone_name


def get_now() -> datetime:
    """
    Joriy vaqtni sozlangan vaqt zonasida qaytaradi (naive datetime).
    datetime.utcnow() o'rniga bu funksiyadan foydalaning.
    """
    tz = pytz.timezone(_timezone_name)
    return datetime.now(tz).replace(tzinfo=None)


def get_today_start() -> datetime:
    """Bugungi kun boshlanishi (00:00:00) sozlangan vaqt zonasida"""
    return get_now().replace(hour=0, minute=0, second=0, microsecond=0)


def get_month_start() -> datetime:
    """Joriy oy boshlanishi sozlangan vaqt zonasida"""
    return get_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


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