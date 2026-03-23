from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User
from app.core.constants import PermissionType, UserRole
from app.core.permissions import has_permission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
    """
    Joriy foydalanuvchini olish
    """
    auth_service = AuthService(db)
    user = auth_service.get_current_user(token)
    return user


def require_permission(permission: PermissionType):
    """
    Permission talab qilish (decorator)
    """

    async def permission_checker(
            current_user: User = Depends(get_current_user)
    ):
        user_role = UserRole(current_user.role.name.lower())

        if not has_permission(user_role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sizda bu amalni bajarish uchun ruxsat yo'q"
            )

        return current_user

    return permission_checker


async def require_admin(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Faqat superadmin va admin uchun (delete operatsiyalari)
    """
    if current_user.role.name.lower() not in ("superadmin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat superadmin va admin o'chirish huquqiga ega"
        )
    return current_user


def require_role(role: UserRole):
    """
    Role talab qilish (decorator)
    """

    async def role_checker(
            current_user: User = Depends(get_current_user)
    ):
        if current_user.role.name.lower() != role.value.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sizda bu amalni bajarish uchun ruxsat yo'q"
            )

        return current_user

    return role_checker