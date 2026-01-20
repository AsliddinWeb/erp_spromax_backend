import re
from typing import Optional


def validate_phone_number(phone: str) -> bool:
    """Telefon raqamni tekshirish (O'zbekiston formati)"""
    pattern = r'^\+998[0-9]{9}$'
    return bool(re.match(pattern, phone))


def validate_email(email: str) -> bool:
    """Email'ni tekshirish"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_inn(inn: str) -> bool:
    """INN (STIR) ni tekshirish (9 raqam)"""
    pattern = r'^[0-9]{9}$'
    return bool(re.match(pattern, inn))


def sanitize_string(text: str) -> str:
    """String'ni tozalash"""
    if not text:
        return ""
    return text.strip()


def validate_positive_number(value: float) -> bool:
    """Musbat sonni tekshirish"""
    return value > 0