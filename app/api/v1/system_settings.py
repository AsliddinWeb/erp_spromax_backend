from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.system_settings import (
    SystemSettingResponse, SystemSettingUpdate,
    TimezoneUpdate, TimezoneInfo, AVAILABLE_TIMEZONES
)
from app.services.system_settings_service import SystemSettingsService
from app.utils.datetime_utils import get_timezone_name
from app.api.v1.auth import oauth2_scheme
from app.services.auth_service import AuthService
from app.core.exceptions import ForbiddenException

router = APIRouter(prefix="/settings", tags=["System Settings"])


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.get_current_user(token)


def require_superadmin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user = auth_service.get_current_user(token)
    if user.role.name != "superadmin":
        raise ForbiddenException(detail="Faqat superadmin ruxsat berilgan")
    return user


# ─── GET all settings ────────────────────────────────────────────────────────
@router.get("", response_model=List[SystemSettingResponse])
async def get_all_settings(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Barcha tizim sozlamalarini olish"""
    allowed = {"superadmin", "admin", "director"}
    if current_user.role.name not in allowed:
        raise ForbiddenException(detail="Ruxsat yo'q")
    service = SystemSettingsService(db)
    return service.get_all()


# ─── GET timezone info ────────────────────────────────────────────────────────
@router.get("/timezone", response_model=dict)
async def get_timezone(current_user=Depends(get_current_user)):
    """Joriy vaqt zonasi"""
    return {
        "timezone": get_timezone_name(),
        "available": [t.model_dump() for t in AVAILABLE_TIMEZONES]
    }


# ─── PUT timezone ─────────────────────────────────────────────────────────────
@router.put("/timezone", response_model=SystemSettingResponse)
async def update_timezone(
    data: TimezoneUpdate,
    current_user=Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Vaqt zonasini o'zgartirish (faqat superadmin)"""
    service = SystemSettingsService(db)
    return service.update_timezone(data.timezone, user_id=current_user.id)


# ─── PUT any setting ──────────────────────────────────────────────────────────
@router.put("/{key}", response_model=SystemSettingResponse)
async def update_setting(
    key: str,
    data: SystemSettingUpdate,
    current_user=Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Istalgan sozlamani yangilash (faqat superadmin)"""
    service = SystemSettingsService(db)
    return service.update_setting(
        key=key,
        value=data.value,
        description=data.description,
        user_id=current_user.id,
    )
