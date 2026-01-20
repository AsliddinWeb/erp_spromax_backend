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

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Yangi foydalanuvchi yaratish
    
    Faqat admin va superadmin ruxsat berilgan.
    """
    # TODO: Permission check qo'shish
    user_service = UserService(db)
    return user_service.create_user(user_data)


@router.get("", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Barcha foydalanuvchilarni olish
    """
    user_service = UserService(db)
    return user_service.get_all_users(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: UUID,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Bitta foydalanuvchini olish
    """
    user_service = UserService(db)
    return user_service.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Foydalanuvchini yangilash
    """
    user_service = UserService(db)
    return user_service.update_user(user_id, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: UUID,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Foydalanuvchini o'chirish (soft delete)
    """
    user_service = UserService(db)
    user_service.delete_user(user_id)
    return {"message": "Foydalanuvchi o'chirildi"}


@router.get("/roles/list", response_model=List[RoleResponse], status_code=status.HTTP_200_OK)
async def get_roles(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Barcha rollarni olish
    """
    role_repo = RoleRepository(db)
    return role_repo.get_all()