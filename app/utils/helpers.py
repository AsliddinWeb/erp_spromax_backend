from decimal import Decimal
from typing import Optional


def calculate_percentage(value: Decimal, total: Decimal) -> Decimal:
    """Foizni hisoblash"""
    if total == 0:
        return Decimal(0)
    return (value / total) * 100


def round_decimal(value: Decimal, places: int = 2) -> Decimal:
    """Decimal'ni yaxlitlash"""
    return round(value, places)


def format_currency(amount: Decimal, currency: str = "UZS") -> str:
    """Pul summasini format qilish"""
    return f"{amount:,.2f} {currency}"


def generate_batch_number() -> str:
    """Partiya raqamini generatsiya qilish"""
    from datetime import datetime
    import random
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = random.randint(1000, 9999)
    return f"BATCH-{timestamp}-{random_part}"


def calculate_efficiency(
    produced: Decimal,
    raw_material_used: Decimal,
    conversion_rate: Decimal
) -> Decimal:
    """Samaradorlikni hisoblash"""
    if raw_material_used == 0 or conversion_rate == 0:
        return Decimal(0)
    
    expected_output = raw_material_used * conversion_rate
    if expected_output == 0:
        return Decimal(0)
    
    efficiency = (produced / expected_output) * 100
    return round_decimal(efficiency)