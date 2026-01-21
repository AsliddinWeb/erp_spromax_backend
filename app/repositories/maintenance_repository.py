from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID
from app.models.maintenance import (
    MaintenanceRequest,
    MaintenanceLog,
    SparePart,
    SparePartUsage,
    MaintenanceSchedule
)
from app.repositories.base import BaseRepository


class MaintenanceRequestRepository(BaseRepository[MaintenanceRequest]):
    def __init__(self, db: Session):
        super().__init__(MaintenanceRequest, db)
    
    def get_with_relations(self, request_id: UUID) -> Optional[MaintenanceRequest]:
        """Relationships bilan so'rov"""
        return self.db.query(MaintenanceRequest).options(
            joinedload(MaintenanceRequest.machine),
            joinedload(MaintenanceRequest.requester),
            joinedload(MaintenanceRequest.technician)
        ).filter(
            MaintenanceRequest.id == request_id,
            MaintenanceRequest.is_active == True
        ).first()
    
    def get_all_with_relations(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        machine_id: Optional[UUID] = None
    ) -> List[MaintenanceRequest]:
        """Barcha so'rovlar"""
        query = self.db.query(MaintenanceRequest).options(
            joinedload(MaintenanceRequest.machine),
            joinedload(MaintenanceRequest.requester)
        ).filter(MaintenanceRequest.is_active == True)
        
        if status:
            query = query.filter(MaintenanceRequest.status == status)
        
        if priority:
            query = query.filter(MaintenanceRequest.priority == priority)
        
        if machine_id:
            query = query.filter(MaintenanceRequest.machine_id == machine_id)
        
        return query.order_by(desc(MaintenanceRequest.requested_date)).offset(skip).limit(limit).all()
    
    def get_by_status(self, status: str) -> List[MaintenanceRequest]:
        """Status bo'yicha so'rovlar"""
        return self.db.query(MaintenanceRequest).filter(
            MaintenanceRequest.status == status,
            MaintenanceRequest.is_active == True
        ).all()
    
    def get_count_by_status(self, status: str) -> int:
        """Status bo'yicha soni"""
        return self.db.query(func.count(MaintenanceRequest.id)).filter(
            MaintenanceRequest.status == status,
            MaintenanceRequest.is_active == True
        ).scalar()


class MaintenanceLogRepository(BaseRepository[MaintenanceLog]):
    def __init__(self, db: Session):
        super().__init__(MaintenanceLog, db)
    
    def get_by_request(self, request_id: UUID) -> List[MaintenanceLog]:
        """So'rov bo'yicha loglar"""
        return self.db.query(MaintenanceLog).options(
            joinedload(MaintenanceLog.performer)
        ).filter(
            MaintenanceLog.request_id == request_id,
            MaintenanceLog.is_active == True
        ).order_by(MaintenanceLog.log_date).all()
    
    def get_total_hours(self) -> Decimal:
        """Umumiy ish soatlari"""
        result = self.db.query(func.sum(MaintenanceLog.hours_spent)).filter(
            MaintenanceLog.is_active == True
        ).scalar()
        return result or Decimal("0")


class SparePartRepository(BaseRepository[SparePart]):
    def __init__(self, db: Session):
        super().__init__(SparePart, db)
    
    def get_by_part_number(self, part_number: str) -> Optional[SparePart]:
        """Part number bo'yicha qism"""
        return self.db.query(SparePart).filter(
            SparePart.part_number == part_number,
            SparePart.is_active == True
        ).first()
    
    def get_low_stock_parts(self) -> List[SparePart]:
        """Kam qolgan qismlar"""
        return self.db.query(SparePart).filter(
            SparePart.quantity_in_stock <= SparePart.min_stock_level,
            SparePart.is_active == True
        ).all()
    
    def get_low_stock_count(self) -> int:
        """Kam qolgan qismlar soni"""
        return self.db.query(func.count(SparePart.id)).filter(
            SparePart.quantity_in_stock <= SparePart.min_stock_level,
            SparePart.is_active == True
        ).scalar()


class SparePartUsageRepository(BaseRepository[SparePartUsage]):
    def __init__(self, db: Session):
        super().__init__(SparePartUsage, db)
    
    def get_by_request(self, request_id: UUID) -> List[SparePartUsage]:
        """So'rov bo'yicha ishlatilgan qismlar"""
        return self.db.query(SparePartUsage).options(
            joinedload(SparePartUsage.spare_part)
        ).filter(
            SparePartUsage.request_id == request_id,
            SparePartUsage.is_active == True
        ).all()


class MaintenanceScheduleRepository(BaseRepository[MaintenanceSchedule]):
    def __init__(self, db: Session):
        super().__init__(MaintenanceSchedule, db)
    
    def get_by_machine(self, machine_id: UUID) -> List[MaintenanceSchedule]:
        """Mashina bo'yicha jadvallar"""
        return self.db.query(MaintenanceSchedule).filter(
            MaintenanceSchedule.machine_id == machine_id,
            MaintenanceSchedule.is_active == 'active'
        ).all()
    
    def get_overdue_schedules(self, today: date) -> List[MaintenanceSchedule]:
        """Muddati o'tgan jadvallar"""
        return self.db.query(MaintenanceSchedule).options(
            joinedload(MaintenanceSchedule.machine)
        ).filter(
            MaintenanceSchedule.next_maintenance_date < today,
            MaintenanceSchedule.is_active == 'active'
        ).all()