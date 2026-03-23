from sqlalchemy.orm import Session
from uuid import UUID
from app.models.system_settings import SystemSettings
from app.utils.datetime_utils import get_now, set_timezone, get_timezone_name
from app.core.exceptions import NotFoundException, BadRequestException
import pytz


# Default sozlamalar
DEFAULT_SETTINGS = {
    "timezone": {
        "value": "Asia/Tashkent",
        "description": "Tizim vaqt zonasi (masalan: Asia/Tashkent, Europe/Moscow, UTC)"
    },
    "company_name": {
        "value": "S PROMAX PLAST",
        "description": "Kompaniya nomi"
    },
    "currency": {
        "value": "UZS",
        "description": "Asosiy valyuta (UZS, USD, EUR)"
    },
    "date_format": {
        "value": "DD.MM.YYYY",
        "description": "Sana formati"
    },
}


class SystemSettingsService:
    def __init__(self, db: Session):
        self.db = db

    def initialize_defaults(self) -> None:
        """Agar sozlamalar yo'q bo'lsa, default qiymatlarni yaratish"""
        for key, data in DEFAULT_SETTINGS.items():
            existing = self.db.query(SystemSettings).filter(
                SystemSettings.key == key
            ).first()
            if not existing:
                setting = SystemSettings(
                    key=key,
                    value=data["value"],
                    description=data["description"],
                    updated_at=get_now(),
                )
                self.db.add(setting)
        self.db.commit()

    def load_timezone_from_db(self) -> str:
        """DB dan timezone ni o'qib, tizimga qo'llash"""
        setting = self.db.query(SystemSettings).filter(
            SystemSettings.key == "timezone"
        ).first()
        if setting:
            try:
                set_timezone(setting.value)
                return setting.value
            except Exception:
                pass
        return get_timezone_name()

    def get_all(self):
        """Barcha sozlamalar"""
        return self.db.query(SystemSettings).order_by(SystemSettings.key).all()

    def get_by_key(self, key: str) -> SystemSettings:
        """Kalit bo'yicha sozlama"""
        setting = self.db.query(SystemSettings).filter(
            SystemSettings.key == key
        ).first()
        if not setting:
            raise NotFoundException(detail=f"'{key}' sozlamasi topilmadi")
        return setting

    def update_setting(self, key: str, value: str, description=None, user_id=None) -> SystemSettings:
        """Sozlamani yangilash"""
        setting = self.db.query(SystemSettings).filter(
            SystemSettings.key == key
        ).first()

        if not setting:
            setting = SystemSettings(
                key=key,
                value=value,
                description=description,
                updated_by_id=user_id,
                updated_at=get_now(),
            )
            self.db.add(setting)
        else:
            setting.value = value
            if description is not None:
                setting.description = description
            setting.updated_by_id = user_id
            setting.updated_at = get_now()

        self.db.commit()
        self.db.refresh(setting)
        return setting

    def update_timezone(self, tz_name: str, user_id=None) -> SystemSettings:
        """Vaqt zonasini o'zgartirish va darhol qo'llash"""
        try:
            pytz.timezone(tz_name)
        except Exception:
            raise BadRequestException(detail=f"Noto'g'ri vaqt zonasi: '{tz_name}'")

        setting = self.update_setting(
            key="timezone",
            value=tz_name,
            description="Tizim vaqt zonasi",
            user_id=user_id,
        )

        # Darhol qo'llash
        set_timezone(tz_name)
        return setting
