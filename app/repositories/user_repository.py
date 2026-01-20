from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from app.models.user import User, Role, Permission
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Username bo'yicha foydalanuvchini olish"""
        return self.db.query(User).options(
            joinedload(User.role).joinedload(Role.permissions)
        ).filter(
            User.username == username.lower(),
            User.is_active == True
        ).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Email bo'yicha foydalanuvchini olish"""
        return self.db.query(User).filter(
            User.email == email.lower(),
            User.is_active == True
        ).first()
    
    def get_with_role(self, user_id: UUID) -> Optional[User]:
        """Role bilan foydalanuvchini olish"""
        return self.db.query(User).options(
            joinedload(User.role).joinedload(Role.permissions)
        ).filter(
            User.id == user_id,
            User.is_active == True
        ).first()
    
    def get_all_with_roles(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Barcha foydalanuvchilarni role bilan olish"""
        return self.db.query(User).options(
            joinedload(User.role)
        ).filter(
            User.is_active == True
        ).offset(skip).limit(limit).all()


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: Session):
        super().__init__(Role, db)
    
    def get_by_name(self, name: str) -> Optional[Role]:
        """Nom bo'yicha rolni olish"""
        return self.db.query(Role).filter(
            Role.name == name,
            Role.is_active == True
        ).first()
    
    def get_with_permissions(self, role_id: UUID) -> Optional[Role]:
        """Permissions bilan rolni olish"""
        return self.db.query(Role).options(
            joinedload(Role.permissions)
        ).filter(
            Role.id == role_id,
            Role.is_active == True
        ).first()


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self, db: Session):
        super().__init__(Permission, db)
    
    def get_by_name(self, name: str) -> Optional[Permission]:
        """Nom bo'yicha permission olish"""
        return self.db.query(Permission).filter(
            Permission.name == name,
            Permission.is_active == True
        ).first()
    
    def get_by_ids(self, permission_ids: List[UUID]) -> List[Permission]:
        """ID'lar bo'yicha permissionlarni olish"""
        return self.db.query(Permission).filter(
            Permission.id.in_(permission_ids),
            Permission.is_active == True
        ).all()