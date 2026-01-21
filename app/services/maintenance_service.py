from typing import List, Optional
from sqlalchemy.orm import Session
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
from app.schemas.maintenance import (
    MaintenanceRequestCreate,
    MaintenanceRequestUpdate,
    MaintenanceLogCreate,
    SparePartCreate,
    SparePartUpdate,
    SparePartUsageCreate,
    MaintenanceScheduleCreate,
    MaintenanceScheduleUpdate,
    MaintenanceStatistics
)
from app.repositories.maintenance_repository import (
    MaintenanceRequestRepository,
    MaintenanceLogRepository,
    SparePartRepository,
    SparePartUsageRepository,
    MaintenanceScheduleRepository
)
from app.repositories.production_repository import MachineRepository
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException,
    InsufficientStockException
)


class MaintenanceService:
    def __init__(self, db: Session):
        self.db = db
        self.request_repo = MaintenanceRequestRepository(db)
        self.log_repo = MaintenanceLogRepository(db)
        self.spare_part_repo = SparePartRepository(db)
        self.usage_repo = SparePartUsageRepository(db)
        self.schedule_repo = MaintenanceScheduleRepository(db)
        self.machine_repo = MachineRepository(db)
    
    # ============ MAINTENANCE REQUEST METHODS ============
    
    def create_request(
        self,
        request_data: MaintenanceRequestCreate,
        user_id: UUID
    ) -> MaintenanceRequest:
        """Yangi texnik xizmat so'rovi"""
        # Mashina tekshirish
        machine = self.machine_repo.get_by_id(request_data.machine_id)
        if not machine:
            raise NotFoundException(detail="Mashina topilmadi")
        
        new_request = MaintenanceRequest(
            machine_id=request_data.machine_id,
            request_type=request_data.request_type,
            priority=request_data.priority,
            description=request_data.description,
            status='pending',
            requested_date=datetime.utcnow(),
            scheduled_date=request_data.scheduled_date,
            requested_by=user_id
        )
        
        # Agar urgent bo'lsa, mashina statusini o'zgartirish
        if request_data.priority == 'urgent':
            machine.status = 'maintenance'
            self.db.commit()
        
        return self.request_repo.create(new_request)
    
    def get_request(self, request_id: UUID) -> MaintenanceRequest:
        """So'rov olish"""
        request = self.request_repo.get_with_relations(request_id)
        if not request:
            raise NotFoundException(detail="So'rov topilmadi")
        return request
    
    def get_all_requests(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        machine_id: Optional[UUID] = None
    ) -> List[MaintenanceRequest]:
        """Barcha so'rovlar"""
        return self.request_repo.get_all_with_relations(
            skip=skip,
            limit=limit,
            status=status,
            priority=priority,
            machine_id=machine_id
        )
    
    def update_request(
        self,
        request_id: UUID,
        request_data: MaintenanceRequestUpdate
    ) -> MaintenanceRequest:
        """So'rov yangilash"""
        request = self.get_request(request_id)
        
        # Status o'zgarsa, mashina statusini yangilash
        if request_data.status:
            if request_data.status == 'in_progress':
                machine = self.machine_repo.get_by_id(request.machine_id)
                machine.status = 'maintenance'
            elif request_data.status == 'completed':
                machine = self.machine_repo.get_by_id(request.machine_id)
                machine.status = 'active'
                request.completed_date = datetime.utcnow()
            
            self.db.commit()
        
        update_data = request_data.model_dump(exclude_unset=True)
        return self.request_repo.update(request, update_data)
    
    def delete_request(self, request_id: UUID) -> bool:
        """So'rov o'chirish"""
        return self.request_repo.delete(request_id)
    
    # ============ MAINTENANCE LOG METHODS ============
    
    def create_log(self, log_data: MaintenanceLogCreate, user_id: UUID) -> MaintenanceLog:
        """Ish jurnali yozish"""
        # So'rov tekshirish
        request = self.get_request(log_data.request_id)
        
        new_log = MaintenanceLog(
            request_id=log_data.request_id,
            log_date=datetime.utcnow(),
            work_description=log_data.work_description,
            hours_spent=log_data.hours_spent,
            notes=log_data.notes,
            performed_by=user_id
        )
        
        return self.log_repo.create(new_log)
    
    def get_request_logs(self, request_id: UUID) -> List[MaintenanceLog]:
        """So'rov loglari"""
        return self.log_repo.get_by_request(request_id)
    
    # ============ SPARE PART METHODS ============
    
    def create_spare_part(self, part_data: SparePartCreate) -> SparePart:
        """Yangi ehtiyot qism qo'shish"""
        if part_data.part_number:
            existing = self.spare_part_repo.get_by_part_number(part_data.part_number)
            if existing:
                raise ConflictException(detail=f"'{part_data.part_number}' raqamli qism mavjud")
        
        new_part = SparePart(**part_data.model_dump())
        return self.spare_part_repo.create(new_part)
    
    def get_spare_part(self, part_id: UUID) -> SparePart:
        """Ehtiyot qism olish"""
        part = self.spare_part_repo.get_by_id(part_id)
        if not part:
            raise NotFoundException(detail="Ehtiyot qism topilmadi")
        return part
    
    def get_all_spare_parts(self, skip: int = 0, limit: int = 100) -> List[SparePart]:
        """Barcha ehtiyot qismlar"""
        return self.spare_part_repo.get_all(skip=skip, limit=limit)
    
    def get_low_stock_parts(self) -> List[SparePart]:
        """Kam qolgan qismlar"""
        return self.spare_part_repo.get_low_stock_parts()
    
    def update_spare_part(self, part_id: UUID, part_data: SparePartUpdate) -> SparePart:
        """Ehtiyot qism yangilash"""
        part = self.get_spare_part(part_id)
        
        if part_data.part_number and part_data.part_number != part.part_number:
            existing = self.spare_part_repo.get_by_part_number(part_data.part_number)
            if existing:
                raise ConflictException(detail=f"'{part_data.part_number}' raqamli qism mavjud")
        
        update_data = part_data.model_dump(exclude_unset=True)
        return self.spare_part_repo.update(part, update_data)
    
    def delete_spare_part(self, part_id: UUID) -> bool:
        """Ehtiyot qism o'chirish"""
        return self.spare_part_repo.delete(part_id)
    
    # ============ SPARE PART USAGE METHODS ============
    
    def create_spare_part_usage(self, usage_data: SparePartUsageCreate) -> SparePartUsage:
        """Ehtiyot qism ishlatish"""
        # So'rov va qism tekshirish
        request = self.get_request(usage_data.request_id)
        part = self.get_spare_part(usage_data.spare_part_id)
        
        # Stock tekshirish
        if part.quantity_in_stock < usage_data.quantity_used:
            raise InsufficientStockException(
                detail=f"Omborda yetarli qism yo'q. Mavjud: {part.quantity_in_stock}"
            )
        
        new_usage = SparePartUsage(
            request_id=usage_data.request_id,
            spare_part_id=usage_data.spare_part_id,
            quantity_used=usage_data.quantity_used,
            usage_date=datetime.utcnow(),
            notes=usage_data.notes
        )
        usage = self.usage_repo.create(new_usage)
        
        # Stock kamaytirish
        part.quantity_in_stock -= usage_data.quantity_used
        self.db.commit()
        
        return usage
    
    def get_request_spare_parts(self, request_id: UUID) -> List[SparePartUsage]:
        """So'rovda ishlatilgan qismlar"""
        return self.usage_repo.get_by_request(request_id)
    
    # ============ MAINTENANCE SCHEDULE METHODS ============
    
    def create_schedule(self, schedule_data: MaintenanceScheduleCreate) -> MaintenanceSchedule:
        """Yangi texnik xizmat jadvali"""
        # Mashina tekshirish
        machine = self.machine_repo.get_by_id(schedule_data.machine_id)
        if not machine:
            raise NotFoundException(detail="Mashina topilmadi")
        
        # Next maintenance date hisoblash
        if schedule_data.last_maintenance_date:
            next_date = schedule_data.last_maintenance_date + timedelta(days=schedule_data.interval_days)
        else:
            next_date = date.today() + timedelta(days=schedule_data.interval_days)
        
        new_schedule = MaintenanceSchedule(
            machine_id=schedule_data.machine_id,
            schedule_type=schedule_data.schedule_type,
            description=schedule_data.description,
            interval_days=schedule_data.interval_days,
            last_maintenance_date=schedule_data.last_maintenance_date,
            next_maintenance_date=next_date,
            is_active='active'
        )
        
        return self.schedule_repo.create(new_schedule)
    
    def get_schedule(self, schedule_id: UUID) -> MaintenanceSchedule:
        """Jadval olish"""
        schedule = self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise NotFoundException(detail="Jadval topilmadi")
        return schedule
    
    def get_all_schedules(self, skip: int = 0, limit: int = 100) -> List[MaintenanceSchedule]:
        """Barcha jadvallar"""
        return self.schedule_repo.get_all(skip=skip, limit=limit)
    
    def get_machine_schedules(self, machine_id: UUID) -> List[MaintenanceSchedule]:
        """Mashina jadvallari"""
        return self.schedule_repo.get_by_machine(machine_id)
    
    def update_schedule(self, schedule_id: UUID, schedule_data: MaintenanceScheduleUpdate) -> MaintenanceSchedule:
        """Jadval yangilash"""
        schedule = self.get_schedule(schedule_id)
        
        # Last maintenance date o'zgarsa, next date qayta hisoblash
        if schedule_data.last_maintenance_date:
            schedule.next_maintenance_date = schedule_data.last_maintenance_date + timedelta(
                days=schedule_data.interval_days or schedule.interval_days
            )
        
        update_data = schedule_data.model_dump(exclude_unset=True)
        return self.schedule_repo.update(schedule, update_data)
    
    def delete_schedule(self, schedule_id: UUID) -> bool:
        """Jadval o'chirish"""
        return self.schedule_repo.delete(schedule_id)
    
    # ============ STATISTICS METHODS ============
    
    def get_statistics(self) -> MaintenanceStatistics:
        """Texnik xizmat statistikasi"""
        total_requests = self.request_repo.count()
        pending_requests = self.request_repo.get_count_by_status('pending')
        in_progress_requests = self.request_repo.get_count_by_status('in_progress')
        completed_requests = self.request_repo.get_count_by_status('completed')
        
        total_spare_parts = self.spare_part_repo.count()
        low_stock_parts = self.spare_part_repo.get_low_stock_count()
        
        total_maintenance_hours = self.log_repo.get_total_hours()
        
        # Texnik xizmatdagi mashinalar
        machines_under_maintenance = len(self.request_repo.get_by_status('in_progress'))
        
        return MaintenanceStatistics(
            total_requests=total_requests,
            pending_requests=pending_requests,
            in_progress_requests=in_progress_requests,
            completed_requests=completed_requests,
            total_spare_parts=total_spare_parts,
            low_stock_parts=low_stock_parts,
            total_maintenance_hours=total_maintenance_hours,
            machines_under_maintenance=machines_under_maintenance
        )