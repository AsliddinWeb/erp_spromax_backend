from typing import Optional, List
from pydantic import Field, field_validator
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from app.schemas.base import BaseSchema, BaseIDSchema


# ============ SHARED INFO SCHEMAS ============

class MachineInfo(BaseSchema):
    id: UUID
    name: str
    serial_number: Optional[str] = None

    model_config = {"from_attributes": True}


class CreatorInfo(BaseSchema):
    id: UUID
    username: str
    full_name: Optional[str] = None
    role: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_validator('role', mode='before')
    @classmethod
    def serialize_role(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return v
        return getattr(v, 'name', None)


# ============ MAINTENANCE REQUEST SCHEMAS ============

class MaintenanceRequestBase(BaseSchema):
    machine_id: UUID
    request_type: str = Field(..., pattern="^(repair|maintenance|inspection)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    description: str = Field(..., min_length=1)
    scheduled_date: Optional[datetime] = None


class MaintenanceRequestCreate(MaintenanceRequestBase):
    pass


class MaintenanceRequestUpdate(BaseSchema):
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    description: Optional[str] = Field(None, min_length=1)
    scheduled_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    assigned_to: Optional[UUID] = None


class MaintenanceRequestResponse(BaseIDSchema):
    machine_id: UUID
    request_type: str
    priority: str
    description: str
    status: str
    requested_date: datetime
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    requested_by: UUID
    assigned_to: Optional[UUID] = None
    machine: Optional[MachineInfo] = None
    requester: Optional[CreatorInfo] = None
    technician: Optional[CreatorInfo] = None

    model_config = {"from_attributes": True}


# ============ MAINTENANCE LOG SCHEMAS ============

class MaintenanceLogBase(BaseSchema):
    work_description: str = Field(..., min_length=1)
    hours_spent: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class MaintenanceLogCreate(MaintenanceLogBase):
    request_id: UUID


class MaintenanceLogResponse(BaseIDSchema, MaintenanceLogBase):
    request_id: UUID
    log_date: datetime
    performed_by: UUID
    performer: Optional[CreatorInfo] = None

    model_config = {"from_attributes": True}


# ============ SPARE PART SCHEMAS ============

class SparePartBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200)
    part_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    unit: str = Field(..., min_length=1, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    quantity_in_stock: Decimal = Field(default=Decimal("0"), ge=0)
    min_stock_level: Decimal = Field(default=Decimal("0"), ge=0)


class SparePartCreate(SparePartBase):
    pass


class SparePartUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    part_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    quantity_in_stock: Optional[Decimal] = Field(None, ge=0)
    min_stock_level: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class SparePartResponse(BaseIDSchema, SparePartBase):
    is_low_stock: Optional[bool] = False

    model_config = {"from_attributes": True}


# ============ SPARE PART USAGE SCHEMAS ============

class SparePartUsageBase(BaseSchema):
    spare_part_id: UUID
    quantity_used: Decimal = Field(..., gt=0)
    notes: Optional[str] = None


class SparePartUsageCreate(SparePartUsageBase):
    request_id: UUID

    @field_validator('quantity_used')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Miqdor musbat bo\'lishi kerak')
        return v


class SparePartUsageResponse(BaseIDSchema, SparePartUsageBase):
    request_id: UUID
    usage_date: datetime
    spare_part: Optional[SparePartResponse] = None

    model_config = {"from_attributes": True}


# ============ MAINTENANCE SCHEDULE SCHEMAS ============

class MaintenanceScheduleBase(BaseSchema):
    machine_id: UUID
    schedule_type: str = Field(..., pattern="^(daily|weekly|monthly|yearly)$")
    description: str = Field(..., min_length=1)
    interval_days: int = Field(..., gt=0)
    last_maintenance_date: Optional[date] = None


class MaintenanceScheduleCreate(MaintenanceScheduleBase):
    pass


class MaintenanceScheduleUpdate(BaseSchema):
    schedule_type: Optional[str] = Field(None, pattern="^(daily|weekly|monthly|yearly)$")
    description: Optional[str] = Field(None, min_length=1)
    interval_days: Optional[int] = Field(None, gt=0)
    last_maintenance_date: Optional[date] = None
    is_active: Optional[str] = Field(None, pattern="^(active|inactive)$")


class MaintenanceScheduleResponse(BaseIDSchema, MaintenanceScheduleBase):
    next_maintenance_date: Optional[date] = None
    is_active: str
    machine: Optional[MachineInfo] = None

    model_config = {"from_attributes": True}


# ============ STATISTICS SCHEMAS ============

class MaintenanceStatistics(BaseSchema):
    total_requests: int
    pending_requests: int
    in_progress_requests: int
    completed_requests: int
    total_spare_parts: int
    low_stock_parts: int
    total_maintenance_hours: Decimal
    machines_under_maintenance: int