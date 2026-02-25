from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.user import User, Role
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.repositories.user_repository import UserRepository, RoleRepository
from app.core.security import get_password_hash
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException
)


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
    
    def create_user(self, user_data: UserCreate) -> User:
        """Yangi foydalanuvchi yaratish"""
        # Username mavjudligini tekshirish
        existing_user = self.user_repo.get_by_username(user_data.username)
        if existing_user:
            raise ConflictException(detail="Bunday username mavjud")
        
        # Email mavjudligini tekshirish
        existing_email = self.user_repo.get_by_email(user_data.email)
        if existing_email:
            raise ConflictException(detail="Bunday email mavjud")
        
        # Role mavjudligini tekshirish
        role = self.role_repo.get_by_id(user_data.role_id)
        if not role:
            raise NotFoundException(detail="Role topilmadi")
        
        # Yangi foydalanuvchi yaratish
        new_user = User(
            username=user_data.username.lower(),
            email=user_data.email.lower(),
            full_name=user_data.full_name,
            phone=user_data.phone,
            hashed_password=get_password_hash(user_data.password),
            role_id=user_data.role_id
        )
        
        return self.user_repo.create(new_user)
    
    def get_user(self, user_id: UUID) -> User:
        """Foydalanuvchini olish"""
        user = self.user_repo.get_with_role(user_id)
        if not user:
            raise NotFoundException(detail="Foydalanuvchi topilmadi")
        return user
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Barcha foydalanuvchilarni olish"""
        return self.user_repo.get_all_with_roles(skip=skip, limit=limit)

    def update_user(self, user_id: UUID, user_data: UserUpdate) -> User:
        """Foydalanuvchini yangilash"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail="Foydalanuvchi topilmadi")

        if user_data.email and user_data.email != user.email:
            existing_email = self.user_repo.get_by_email(user_data.email)
            if existing_email:
                raise ConflictException(detail="Bunday email mavjud")

        if user_data.role_id:
            role = self.role_repo.get_by_id(user_data.role_id)
            if not role:
                raise NotFoundException(detail="Role topilmadi")

        update_data = user_data.model_dump(exclude_unset=True)

        # Password hash qilish
        if 'password' in update_data and update_data['password']:
            update_data['hashed_password'] = get_password_hash(update_data.pop('password'))
        else:
            update_data.pop('password', None)

        return self.user_repo.update(user, update_data)

    def delete_user(self, user_id: UUID) -> bool:
        """Foydalanuvchini o'chirish (hard delete)"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail="Foydalanuvchi topilmadi")
        self.db.delete(user)
        self.db.commit()
        return True
    
    def get_user_count(self) -> int:
        """Foydalanuvchilar sonini olish"""
        return self.user_repo.count()