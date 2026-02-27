from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import LoginRequest, TokenResponse, ChangePasswordRequest
from app.repositories.user_repository import UserRepository
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.exceptions import UnauthorizedException, BadRequestException


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def login(self, login_data: LoginRequest) -> TokenResponse:
        """Login qilish"""
        # Foydalanuvchini topish
        user = self.user_repo.get_by_username(login_data.username)

        if not user:
            raise UnauthorizedException(detail="Username yoki parol noto'g'ri")

        # Parolni tekshirish
        if not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedException(detail="Username yoki parol noto'g'ri")

        # Tokenlar yaratish
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.name
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Token'ni yangilash"""
        # Token'ni decode qilish
        payload = decode_token(refresh_token)

        if not payload:
            raise UnauthorizedException(detail="Token yaroqsiz")

        # Foydalanuvchini tekshirish
        user_id = payload.get("sub")
        user = self.user_repo.get_with_role(user_id)

        if not user:
            raise UnauthorizedException(detail="Foydalanuvchi topilmadi")

        # Yangi tokenlar yaratish
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.name
        }

        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token
        )

    def update_profile(self, user_id: str, data) -> User:
        """Profil ma'lumotlarini yangilash"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise BadRequestException(detail="Foydalanuvchi topilmadi")
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.email is not None:
            user.email = data.email
        if data.phone is not None:
            user.phone = data.phone
        self.db.commit()
        self.db.refresh(user)
        return self.user_repo.get_with_role(str(user.id))

    def change_password(
            self,
            user_id: str,
            password_data: ChangePasswordRequest
    ) -> bool:
        """Parolni o'zgartirish"""
        # Foydalanuvchini topish
        user = self.user_repo.get_by_id(user_id)

        if not user:
            raise BadRequestException(detail="Foydalanuvchi topilmadi")

        # Eski parolni tekshirish
        if not verify_password(password_data.old_password, user.hashed_password):
            raise BadRequestException(detail="Eski parol noto'g'ri")

        # Yangi parolni hash qilish va saqlash
        user.hashed_password = get_password_hash(password_data.new_password)
        self.db.commit()

        return True

    def get_current_user(self, token: str) -> Optional[User]:
        """Token orqali joriy foydalanuvchini olish"""
        payload = decode_token(token)

        if not payload:
            raise UnauthorizedException(detail="Token yaroqsiz")

        user_id = payload.get("sub")
        user = self.user_repo.get_with_role(user_id)

        if not user:
            raise UnauthorizedException(detail="Foydalanuvchi topilmadi")

        return user