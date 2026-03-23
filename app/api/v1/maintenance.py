from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.schemas.maintenance import (
    # Request
    MaintenanceRequestCreate,
    MaintenanceRequestUpdate,
    MaintenanceRequestResponse,
    # Log
    MaintenanceLogCreate,
    MaintenanceLogResponse,
    # Spare Part
    SparePartCreate,
    SparePartUpdate,
    SparePartResponse,
    # Spare Part Usage
    SparePartUsageCreate,
    SparePartUsageResponse,
    # Schedule
    MaintenanceScheduleCreate,
    MaintenanceScheduleUpdate,
    MaintenanceScheduleResponse,
    # Statistics
    MaintenanceStatistics
)
from app.services.maintenance_service import MaintenanceService
from app.dependencies import get_current_user, require_permission, require_admin
from app.models.user import User
from app.core.constants import PermissionType

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


# ============ MAINTENANCE REQUEST ENDPOINTS ============

@router.post("/requests", response_model=MaintenanceRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    request_data: MaintenanceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Texnik xizmat so'rovi yaratish
    
    Operator yoki rahbar uskunaga texnik xizmat kerakligini bildiradi.
    """
    service = MaintenanceService(db)
    return service.create_request(request_data, current_user.id)


@router.get("/requests", response_model=List[MaintenanceRequestResponse])
async def get_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(pending|in_progress|completed|cancelled)$"),
    priority: Optional[str] = Query(None, pattern="^(low|medium|high|urgent)$"),
    machine_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Barcha texnik xizmat so'rovlari
    
    Filtrlash: holat, muhimlik, mashina
    """
    service = MaintenanceService(db)
    return service.get_all_requests(
        skip=skip,
        limit=limit,
        status=status,
        priority=priority,
        machine_id=machine_id
    )


@router.get("/requests/{request_id}", response_model=MaintenanceRequestResponse)
async def get_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bitta so'rov ma'lumotlari"""
    service = MaintenanceService(db)
    return service.get_request(request_id)


@router.put("/requests/{request_id}", response_model=MaintenanceRequestResponse)
async def update_request(
    request_id: UUID,
    request_data: MaintenanceRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    So'rov yangilash
    
    Status o'zgarishi bilan mashina holati avtomatik yangilanadi.
    """
    service = MaintenanceService(db)
    return service.update_request(request_id, request_data)


@router.delete("/requests/{request_id}", status_code=status.HTTP_200_OK)
async def delete_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """So'rov o'chirish"""
    service = MaintenanceService(db)
    service.delete_request(request_id)
    return {"message": "So'rov o'chirildi"}


# ============ MAINTENANCE LOG ENDPOINTS ============

@router.post("/logs", response_model=MaintenanceLogResponse, status_code=status.HTTP_201_CREATED)
async def create_log(
    log_data: MaintenanceLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ish jurnali yozish
    
    Texnik xodim bajarilgan ishlarni jurnaliga yozadi.
    """
    service = MaintenanceService(db)
    return service.create_log(log_data, current_user.id)


@router.delete("/logs/{log_id}", status_code=status.HTTP_200_OK)
async def delete_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Ish jurnal yozuvini o'chirish (faqat admin)"""
    service = MaintenanceService(db)
    service.delete_log(log_id)
    return {"message": "Jurnal yozuvi o'chirildi"}


@router.get("/requests/{request_id}/logs", response_model=List[MaintenanceLogResponse])
async def get_request_logs(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """So'rov bo'yicha ish jurnali"""
    service = MaintenanceService(db)
    return service.get_request_logs(request_id)


# ============ SPARE PART ENDPOINTS ============

@router.post("/spare-parts", response_model=SparePartResponse, status_code=status.HTTP_201_CREATED)
async def create_spare_part(
    part_data: SparePartCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.WRITE_MAINTENANCE))
):
    """Yangi ehtiyot qism qo'shish"""
    service = MaintenanceService(db)
    return service.create_spare_part(part_data)


@router.get("/spare-parts", response_model=List[SparePartResponse])
async def get_spare_parts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Barcha ehtiyot qismlar ro'yxati"""
    service = MaintenanceService(db)
    parts = service.get_all_spare_parts(skip=skip, limit=limit)
    
    # is_low_stock flagini qo'shish
    for part in parts:
        part.is_low_stock = part.quantity_in_stock <= part.min_stock_level
    
    return parts


@router.get("/spare-parts/low-stock", response_model=List[SparePartResponse])
async def get_low_stock_parts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kam qolgan ehtiyot qismlar"""
    service = MaintenanceService(db)
    parts = service.get_low_stock_parts()
    
    for part in parts:
        part.is_low_stock = True
    
    return parts


@router.get("/spare-parts/{part_id}", response_model=SparePartResponse)
async def get_spare_part(
    part_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bitta ehtiyot qism ma'lumotlari"""
    service = MaintenanceService(db)
    part = service.get_spare_part(part_id)
    part.is_low_stock = part.quantity_in_stock <= part.min_stock_level
    return part


@router.put("/spare-parts/{part_id}", response_model=SparePartResponse)
async def update_spare_part(
    part_id: UUID,
    part_data: SparePartUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.WRITE_MAINTENANCE))
):
    """Ehtiyot qism yangilash"""
    service = MaintenanceService(db)
    return service.update_spare_part(part_id, part_data)


@router.delete("/spare-parts/{part_id}", status_code=status.HTTP_200_OK)
async def delete_spare_part(
    part_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Ehtiyot qism o'chirish"""
    service = MaintenanceService(db)
    service.delete_spare_part(part_id)
    return {"message": "Ehtiyot qism o'chirildi"}


# ============ SPARE PART USAGE ENDPOINTS ============

@router.post("/spare-part-usage", response_model=SparePartUsageResponse, status_code=status.HTTP_201_CREATED)
async def create_spare_part_usage(
    usage_data: SparePartUsageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ehtiyot qism ishlatish
    
    Texnik xizmat jarayonida ehtiyot qism ishlatilganini yozish.
    """
    service = MaintenanceService(db)
    return service.create_spare_part_usage(usage_data)


@router.delete("/spare-part-usage/{usage_id}", status_code=status.HTTP_200_OK)
async def delete_spare_part_usage(
    usage_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Ehtiyot qism ishlatish yozuvini o'chirish (faqat admin)"""
    service = MaintenanceService(db)
    service.delete_spare_part_usage(usage_id)
    return {"message": "Yozuv o'chirildi"}


@router.get("/requests/{request_id}/spare-parts", response_model=List[SparePartUsageResponse])
async def get_request_spare_parts(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """So'rovda ishlatilgan ehtiyot qismlar"""
    service = MaintenanceService(db)
    return service.get_request_spare_parts(request_id)


# ============ MAINTENANCE SCHEDULE ENDPOINTS ============

@router.post("/schedules", response_model=MaintenanceScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: MaintenanceScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.WRITE_MAINTENANCE))
):
    """
    Yangi texnik xizmat jadvali
    
    Mashina uchun rejali texnik xizmat jadvali yaratish.
    """
    service = MaintenanceService(db)
    return service.create_schedule(schedule_data)


@router.get("/schedules", response_model=List[MaintenanceScheduleResponse])
async def get_schedules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Barcha texnik xizmat jadvallari"""
    service = MaintenanceService(db)
    return service.get_all_schedules(skip=skip, limit=limit)


@router.get("/schedules/{schedule_id}", response_model=MaintenanceScheduleResponse)
async def get_schedule(
    schedule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bitta jadval ma'lumotlari"""
    service = MaintenanceService(db)
    return service.get_schedule(schedule_id)


@router.get("/machines/{machine_id}/schedules", response_model=List[MaintenanceScheduleResponse])
async def get_machine_schedules(
    machine_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mashina uchun barcha jadvallar"""
    service = MaintenanceService(db)
    return service.get_machine_schedules(machine_id)


@router.put("/schedules/{schedule_id}", response_model=MaintenanceScheduleResponse)
async def update_schedule(
    schedule_id: UUID,
    schedule_data: MaintenanceScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.WRITE_MAINTENANCE))
):
    """Jadval yangilash"""
    service = MaintenanceService(db)
    return service.update_schedule(schedule_id, schedule_data)


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_200_OK)
async def delete_schedule(
    schedule_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Jadval o'chirish"""
    service = MaintenanceService(db)
    service.delete_schedule(schedule_id)
    return {"message": "Jadval o'chirildi"}


# ============ STATISTICS ENDPOINT ============

@router.get("/statistics", response_model=MaintenanceStatistics)
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Texnik xizmat statistikasi"""
    service = MaintenanceService(db)
    return service.get_statistics()