from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from decimal import Decimal
from app.utils.datetime_utils import get_today_start
from uuid import UUID
from app.models.production import (
    ProductionLine,
    Machine,
    FinishedProduct,
    Shift,
    ShiftMachine,
    ProductionRecord,
    ProductionOutput,
    DefectReason,
    DefectiveProduct,
    ShiftHandover,
    FinishedProductStock
)
from app.repositories.base import BaseRepository


class ProductionLineRepository(BaseRepository[ProductionLine]):
    def __init__(self, db: Session):
        super().__init__(ProductionLine, db)
    
    def get_by_name(self, name: str) -> Optional[ProductionLine]:
        """Nom bo'yicha liniya topish"""
        return self.db.query(ProductionLine).filter(
            ProductionLine.name == name,
            ProductionLine.is_active == True
        ).first()


class MachineRepository(BaseRepository[Machine]):
    def __init__(self, db: Session):
        super().__init__(Machine, db)
    
    def get_by_line(self, line_id: UUID) -> List[Machine]:
        """Liniya bo'yicha mashinalar"""
        return self.db.query(Machine).filter(
            Machine.production_line_id == line_id,
            Machine.is_active == True
        ).all()
    
    def get_active_machines(self) -> List[Machine]:
        """Faol mashinalar"""
        return self.db.query(Machine).filter(
            Machine.status == 'active',
            Machine.is_active == True
        ).all()


class FinishedProductRepository(BaseRepository[FinishedProduct]):
    def __init__(self, db: Session):
        super().__init__(FinishedProduct, db)
    
    def get_by_name(self, name: str) -> Optional[FinishedProduct]:
        """Nom bo'yicha mahsulot topish"""
        return self.db.query(FinishedProduct).filter(
            FinishedProduct.name == name,
            FinishedProduct.is_active == True
        ).first()
    
    def get_all_with_stock(self, skip: int = 0, limit: int = 100) -> List[FinishedProduct]:
        """Barcha mahsulotlar stock bilan"""
        return self.db.query(FinishedProduct).options(
            joinedload(FinishedProduct.finished_product_stock)
        ).filter(
            FinishedProduct.is_active == True
        ).offset(skip).limit(limit).all()


class ShiftRepository(BaseRepository[Shift]):
    def __init__(self, db: Session):
        super().__init__(Shift, db)
    
    def get_with_relations(self, shift_id: UUID) -> Optional[Shift]:
        """Barcha relationship bilan shift"""
        return self.db.query(Shift).options(
            joinedload(Shift.production_line),
            joinedload(Shift.operator),
            joinedload(Shift.shift_machines).joinedload(ShiftMachine.machine)
        ).filter(
            Shift.id == shift_id,
            Shift.is_active == True
        ).first()
    
    def get_active_shifts(self) -> List[Shift]:
        """Faol smenalar"""
        return self.db.query(Shift).filter(
            Shift.status == 'active',
            Shift.is_active == True
        ).all()
    
    def get_by_operator(self, operator_id: UUID, skip: int = 0, limit: int = 100) -> List[Shift]:
        """Operator smenalari"""
        return self.db.query(Shift).options(
            joinedload(Shift.production_line)
        ).filter(
            Shift.operator_id == operator_id,
            Shift.is_active == True
        ).order_by(desc(Shift.start_time)).offset(skip).limit(limit).all()
    
    def get_completed_today(self) -> int:
        """Bugun tugallangan smenalar soni"""
        today_start = get_today_start()
        
        return self.db.query(func.count(Shift.id)).filter(
            Shift.status == 'completed',
            Shift.end_time >= today_start,
            Shift.is_active == True
        ).scalar()


class ProductionRecordRepository(BaseRepository[ProductionRecord]):
    def __init__(self, db: Session):
        super().__init__(ProductionRecord, db)
    
    def get_by_shift(self, shift_id: UUID) -> List[ProductionRecord]:
        """Smena bo'yicha xom-ashyo ishlatish"""
        return self.db.query(ProductionRecord).options(
            joinedload(ProductionRecord.raw_material)
        ).filter(
            ProductionRecord.shift_id == shift_id,
            ProductionRecord.is_active == True
        ).all()
    
    def get_total_used_in_shift(self, shift_id: UUID) -> Decimal:
        """Smenada ishlatilgan umumiy xom-ashyo (kg)"""
        result = self.db.query(
            func.sum(ProductionRecord.quantity_used)
        ).filter(
            ProductionRecord.shift_id == shift_id,
            ProductionRecord.is_active == True
        ).scalar()
        
        return result or Decimal("0")


class ProductionOutputRepository(BaseRepository[ProductionOutput]):
    def __init__(self, db: Session):
        super().__init__(ProductionOutput, db)
    
    def get_by_shift(self, shift_id: UUID) -> List[ProductionOutput]:
        """Smena bo'yicha ishlab chiqarish"""
        return self.db.query(ProductionOutput).options(
            joinedload(ProductionOutput.finished_product)
        ).filter(
            ProductionOutput.shift_id == shift_id,
            ProductionOutput.is_active == True
        ).all()
    
    def get_total_output_in_shift(self, shift_id: UUID) -> Decimal:
        """Smenada ishlab chiqarilgan umumiy mahsulot"""
        result = self.db.query(
            func.sum(ProductionOutput.quantity_produced)
        ).filter(
            ProductionOutput.shift_id == shift_id,
            ProductionOutput.is_active == True
        ).scalar()
        
        return result or Decimal("0")
    
    def get_total_output_today(self) -> Decimal:
        """Bugun ishlab chiqarilgan umumiy mahsulot"""
        today_start = get_today_start()
        
        result = self.db.query(
            func.sum(ProductionOutput.quantity_produced)
        ).filter(
            ProductionOutput.produced_at >= today_start,
            ProductionOutput.is_active == True
        ).scalar()
        
        return result or Decimal("0")


class DefectReasonRepository(BaseRepository[DefectReason]):
    def __init__(self, db: Session):
        super().__init__(DefectReason, db)
    
    def get_by_name(self, name: str) -> Optional[DefectReason]:
        """Nom bo'yicha brak sababi"""
        return self.db.query(DefectReason).filter(
            DefectReason.name == name,
            DefectReason.is_active == True
        ).first()


class DefectiveProductRepository(BaseRepository[DefectiveProduct]):
    def __init__(self, db: Session):
        super().__init__(DefectiveProduct, db)
    
    def get_by_shift(self, shift_id: UUID) -> List[DefectiveProduct]:
        """Smena bo'yicha braklar"""
        return self.db.query(DefectiveProduct).options(
            joinedload(DefectiveProduct.finished_product),
            joinedload(DefectiveProduct.defect_reason)
        ).filter(
            DefectiveProduct.shift_id == shift_id,
            DefectiveProduct.is_active == True
        ).all()
    
    def get_total_defects_in_shift(self, shift_id: UUID) -> Decimal:
        """Smenadagi umumiy brak"""
        result = self.db.query(
            func.sum(DefectiveProduct.quantity)
        ).filter(
            DefectiveProduct.shift_id == shift_id,
            DefectiveProduct.is_active == True
        ).scalar()
        
        return result or Decimal("0")
    
    def get_total_defects_today(self) -> Decimal:
        """Bugüngi umumiy brak"""
        today_start = get_today_start()
        
        result = self.db.query(
            func.sum(DefectiveProduct.quantity)
        ).filter(
            DefectiveProduct.recorded_at >= today_start,
            DefectiveProduct.is_active == True
        ).scalar()
        
        return result or Decimal("0")


class ShiftHandoverRepository(BaseRepository[ShiftHandover]):
    def __init__(self, db: Session):
        super().__init__(ShiftHandover, db)
    
    def get_by_shift(self, shift_id: UUID) -> Optional[ShiftHandover]:
        """Smena bo'yicha topshirish"""
        return self.db.query(ShiftHandover).filter(
            ShiftHandover.shift_id == shift_id,
            ShiftHandover.is_active == True
        ).first()


class FinishedProductStockRepository(BaseRepository[FinishedProductStock]):
    def __init__(self, db: Session):
        super().__init__(FinishedProductStock, db)
    
    def get_by_product(self, product_id: UUID) -> Optional[FinishedProductStock]:
        """Mahsulot bo'yicha qoldiq"""
        return self.db.query(FinishedProductStock).filter(
            FinishedProductStock.finished_product_id == product_id,
            FinishedProductStock.is_active == True
        ).first()
    
    def get_all_with_products(self, skip: int = 0, limit: int = 100) -> List[FinishedProductStock]:
        """Barcha qoldiqlar mahsulot bilan"""
        return self.db.query(FinishedProductStock).options(
            joinedload(FinishedProductStock.finished_product)
        ).filter(
            FinishedProductStock.is_active == True
        ).offset(skip).limit(limit).all()