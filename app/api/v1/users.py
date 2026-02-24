from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse, RoleResponse
from app.services.user_service import UserService
from app.repositories.user_repository import RoleRepository
from app.api.v1.auth import oauth2_scheme
from app.services.auth_service import AuthService
from app.core.exceptions import ForbiddenException

router = APIRouter(prefix="/users", tags=["Users"])


# ============ HELPER ============

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Token orqali joriy foydalanuvchini olish"""
    auth_service = AuthService(db)
    return auth_service.get_current_user(token)


def require_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Faqat admin va superadmin uchun"""
    auth_service = AuthService(db)
    user = auth_service.get_current_user(token)
    allowed_roles = {"admin", "superadmin"}
    if user.role.name not in allowed_roles:
        raise ForbiddenException(detail="Faqat admin va superadmin ruxsat berilgan")
    return user


def require_superadmin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Faqat superadmin uchun"""
    auth_service = AuthService(db)
    user = auth_service.get_current_user(token)
    if user.role.name != "superadmin":
        raise ForbiddenException(detail="Faqat superadmin ruxsat berilgan")
    return user


# ============ ENDPOINTS ============

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user=Depends(require_admin),  # BUG FIX: faqat admin/superadmin
    db: Session = Depends(get_db)
):
    """
    Yangi foydalanuvchi yaratish

    Faqat admin va superadmin ruxsat berilgan.
    """
    user_service = UserService(db)
    return user_service.create_user(user_data)


@router.get("", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user=Depends(require_admin),  # BUG FIX: faqat admin/superadmin
    db: Session = Depends(get_db)
):
    """
    Barcha foydalanuvchilarni olish

    Faqat admin va superadmin ruxsat berilgan.
    """
    user_service = UserService(db)
    return user_service.get_all_users(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: UUID,
    current_user=Depends(get_current_user),  # Har qanday login bo'lgan user o'zini ko'ra oladi
    db: Session = Depends(get_db)
):
    """
    Bitta foydalanuvchini olish

    O'z profilini ko'rish yoki admin boshqasini ko'rishi mumkin.
    """
    # O'zining profilinimi yoki admin/superadmin
    if str(current_user.id) != str(user_id) and current_user.role.name not in {"admin", "superadmin"}:
        raise ForbiddenException(detail="Boshqa foydalanuvchini ko'rishga ruxsat yo'q")

    user_service = UserService(db)
    return user_service.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user=Depends(get_current_user),  # O'zini yoki admin yangilashi mumkin
    db: Session = Depends(get_db)
):
    """
    Foydalanuvchini yangilash

    Foydalanuvchi o'zini, admin/superadmin istalgan userni yangilashi mumkin.
    """
    if str(current_user.id) != str(user_id) and current_user.role.name not in {"admin", "superadmin"}:
        raise ForbiddenException(detail="Boshqa foydalanuvchini yangilashga ruxsat yo'q")

    user_service = UserService(db)
    return user_service.update_user(user_id, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: UUID,
    current_user=Depends(require_superadmin),  # Faqat superadmin o'chira oladi
    db: Session = Depends(get_db)
):
    """
    Foydalanuvchini o'chirish (soft delete)

    Faqat superadmin ruxsat berilgan.
    """
    # O'zini o'chirishdan himoya
    if str(current_user.id) == str(user_id):
        raise ForbiddenException(detail="O'zingizni o'chira olmaysiz")

    user_service = UserService(db)
    user_service.delete_user(user_id)
    return {"message": "Foydalanuvchi o'chirildi"}


@router.get("/roles/list", response_model=List[RoleResponse], status_code=status.HTTP_200_OK)
async def get_roles(
    current_user=Depends(require_admin),  # Faqat admin/superadmin rollar ro'yxatini ko'radi
    db: Session = Depends(get_db)
):
    """
    Barcha rollarni olish

    Faqat admin va superadmin ruxsat berilgan.
    """
    role_repo = RoleRepository(db)
    return role_repo.get_all()