from typing import Optional, List
from pydantic import EmailStr, Field, field_validator
from uuid import UUID
from app.schemas.base import BaseSchema, BaseIDSchema
from app.core.constants import UserRole


# Permission Schemas
class PermissionBase(BaseSchema):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)


class PermissionCreate(PermissionBase):
    pass


class PermissionResponse(BaseIDSchema, PermissionBase):
    pass


# Role Schemas
class RoleBase(BaseSchema):
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class RoleCreate(RoleBase):
    permission_ids: List[UUID] = Field(default_factory=list)


class RoleResponse(BaseIDSchema, RoleBase):
    permissions: List[PermissionResponse] = []


# User Schemas
class UserBase(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username faqat harflar va raqamlardan iborat bo\'lishi kerak')
        return v.lower()


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    role_id: UUID
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Parol kamida bitta katta harf o\'z ichiga olishi kerak')
        if not any(c.islower() for c in v):
            raise ValueError('Parol kamida bitta kichik harf o\'z ichiga olishi kerak')
        if not any(c.isdigit() for c in v):
            raise ValueError('Parol kamida bitta raqam o\'z ichiga olishi kerak')
        return v


class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class UserResponse(BaseIDSchema, UserBase):
    role_id: UUID
    role: Optional[RoleResponse] = None


class UserListResponse(BaseSchema):
    users: List[UserResponse]
    total: int


# Auth Schemas
class LoginRequest(BaseSchema):
    username: str
    password: str


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


class ChangePasswordRequest(BaseSchema):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Parol kamida bitta katta harf o\'z ichiga olishi kerak')
        if not any(c.islower() for c in v):
            raise ValueError('Parol kamida bitta kichik harf o\'z ichiga olishi kerak')
        if not any(c.isdigit() for c in v):
            raise ValueError('Parol kamida bitta raqam o\'z ichiga olishi kerak')
        return v