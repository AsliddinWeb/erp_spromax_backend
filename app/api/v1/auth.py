from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.rate_limit import limiter
from app.schemas.user import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    UpdateProfileRequest,
    UserResponse
)
from app.services.auth_service import AuthService
from app.core.exceptions import UnauthorizedException

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def login(
        request: Request,
        login_data: LoginRequest,
        db: Session = Depends(get_db)
):
    """
    Login qilish

    - **username**: Foydalanuvchi nomi
    - **password**: Parol
    """
    auth_service = AuthService(db)
    return auth_service.login(login_data)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
        token_data: RefreshTokenRequest,
        db: Session = Depends(get_db)
):
    """
    Token'ni yangilash

    - **refresh_token**: Refresh token
    """
    auth_service = AuthService(db)
    return auth_service.refresh_token(token_data.refresh_token)


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    """
    Joriy foydalanuvchi ma'lumotlarini olish
    """
    auth_service = AuthService(db)
    user = auth_service.get_current_user(token)
    return user


@router.put("/me", response_model=UserResponse, status_code=200)
async def update_profile(
        profile_data: UpdateProfileRequest,
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    """Profil ma'lumotlarini yangilash"""
    auth_service = AuthService(db)
    user = auth_service.get_current_user(token)
    return auth_service.update_profile(str(user.id), profile_data)


@router.put("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
        password_data: ChangePasswordRequest,
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    """
    Parolni o'zgartirish

    - **old_password**: Eski parol
    - **new_password**: Yangi parol
    """
    auth_service = AuthService(db)
    user = auth_service.get_current_user(token)

    auth_service.change_password(str(user.id), password_data)

    return {"message": "Parol muvaffaqiyatli o'zgartirildi"}


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    """
    Logout qilish

    Note: JWT stateless bo'lgani uchun, logout client tomonda
    token'ni o'chirish orqali amalga oshiriladi.
    """
    return {"message": "Logout successful"}