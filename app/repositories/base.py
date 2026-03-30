from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from uuid import UUID
from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository class"""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """ID bo'yicha olish"""
        return self.db.query(self.model).filter(
            self.model.id == id,
            self.model.is_active == True
        ).first()
    
    def get_by_id_any(self, id: UUID) -> Optional[ModelType]:
        """ID bo'yicha olish (is_active hisobga olinmaydi)"""
        return self.db.query(self.model).filter(
            self.model.id == id
        ).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Barchasini olish (pagination bilan)"""
        return self.db.query(self.model).filter(
            self.model.is_active == True
        ).offset(skip).limit(limit).all()
    
    def count(self) -> int:
        """Jami soni"""
        return self.db.query(func.count(self.model.id)).filter(
            self.model.is_active == True
        ).scalar()
    
    def create(self, obj_in: ModelType) -> ModelType:
        """Yaratish"""
        self.db.add(obj_in)
        self.db.commit()
        self.db.refresh(obj_in)
        return obj_in
    
    def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        """Yangilash"""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: UUID) -> bool:
        """O'chirish (soft delete)"""
        db_obj = self.get_by_id(id)
        if db_obj:
            db_obj.is_active = False
            self.db.commit()
            return True
        return False
    
    def hard_delete(self, id: UUID) -> bool:
        """O'chirish (hard delete)"""
        db_obj = self.get_by_id(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False