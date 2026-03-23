from typing import Optional, List
from pydantic import BaseModel, field_validator
from datetime import datetime
from uuid import UUID
import pytz


class SystemSettingResponse(BaseModel):
    id: UUID
    key: str
    value: str
    description: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by_id: Optional[UUID] = None

    model_config = {"from_attributes": True}


class SystemSettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None


class TimezoneUpdate(BaseModel):
    timezone: str

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v):
        try:
            pytz.timezone(v)
        except Exception:
            raise ValueError(f"Noto'g'ri vaqt zonasi: {v}")
        return v


class TimezoneInfo(BaseModel):
    timezone: str
    offset: str
    description: str


AVAILABLE_TIMEZONES: List[TimezoneInfo] = [
    TimezoneInfo(timezone="Asia/Tashkent",   offset="UTC+5",  description="Toshkent (O'zbekiston)"),
    TimezoneInfo(timezone="Asia/Almaty",     offset="UTC+5",  description="Olma-Ota (Qozog'iston)"),
    TimezoneInfo(timezone="Asia/Bishkek",    offset="UTC+6",  description="Bishkek (Qirg'iziston)"),
    TimezoneInfo(timezone="Asia/Dushanbe",   offset="UTC+5",  description="Dushanbe (Tojikiston)"),
    TimezoneInfo(timezone="Asia/Ashgabat",   offset="UTC+5",  description="Ashgabat (Turkmaniston)"),
    TimezoneInfo(timezone="Europe/Moscow",   offset="UTC+3",  description="Moskva (Rossiya)"),
    TimezoneInfo(timezone="UTC",             offset="UTC+0",  description="UTC (Universal)"),
]
