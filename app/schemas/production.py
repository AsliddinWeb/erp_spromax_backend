from typing import Optional, List
from pydantic import Field, field_validator
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from app.schemas.base import BaseSchema, BaseIDSchema


# ============ PRODUCTION LINE SCHEMAS ============

class ProductionLineBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    capacity_per_hour: Optional[Decimal] = Field(None, ge=0)


class ProductionLineCreate(ProductionLineBase):
    pass


class ProductionLineUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    capacity_per_hour: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductionLineResponse(BaseIDSchema, ProductionLineBase):
    pass


# ============ MACHINE SCHEMAS ============

class MachineBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    production_line_id: UUID
    status: str = Field(default="active", pattern="^(active|maintenance|broken)$")


class MachineCreate(MachineBase):
    pass


class MachineUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    production_line_id: Optional[UUID] = None
    status: Optional[str] = Field(None, pattern="^(active|maintenance|broken)$")
    is_active: Optional[bool] = None


class MachineResponse(BaseIDSchema, MachineBase):
    production_line: Optional[ProductionLineResponse] = None


# ============ FINISHED PRODUCT SCHEMAS ============

class FinishedProductBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    unit: str = Field(..., min_length=1, max_length=20)
    standard_price: Optional[Decimal] = Field(None, ge=0)


class FinishedProductCreate(FinishedProductBase):
    pass


class FinishedProductUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    standard_price: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class FinishedProductResponse(BaseIDSchema, FinishedProductBase):
    current_stock: Optional[Decimal] = None


# ============ OPERATOR INFO (Shift uchun) ============

class OperatorInfo(BaseSchema):
    id: UUID
    username: str
    full_name: Optional[str] = None
    role: Optional[str] = None  # Role.name (string)

    model_config = {"from_attributes": True}

    @field_validator('role', mode='before')
    @classmethod
    def serialize_role(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return v
        # Role object kelsa .name ni olamiz
        return getattr(v, 'name', None)


# ============ SHIFT SCHEMAS ============

class ShiftBase(BaseSchema):
    production_line_id: UUID
    start_time: datetime
    notes: Optional[str] = None


class ShiftCreate(ShiftBase):
    machine_ids: List[UUID] = Field(default_factory=list)


class ShiftComplete(BaseSchema):
    end_time: datetime
    notes: Optional[str] = None


class ShiftResponse(BaseIDSchema):
    production_line_id: UUID
    operator_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    notes: Optional[str] = None
    production_line: Optional[ProductionLineResponse] = None
    operator: Optional[OperatorInfo] = None
    machines: Optional[List[MachineResponse]] = None

    model_config = {"from_attributes": True}


# ============ PRODUCTION RECORD SCHEMAS ============

class ProductionRecordBase(BaseSchema):
    raw_material_id: UUID
    quantity_used: Decimal = Field(..., gt=0)
    notes: Optional[str] = None


class ProductionRecordCreate(ProductionRecordBase):
    @field_validator('quantity_used')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Miqdor musbat bo\'lishi kerak')
        return v


class ProductionRecordResponse(BaseIDSchema):
    shift_id: UUID
    raw_material_id: UUID
    quantity_used: Decimal
    recorded_at: datetime
    notes: Optional[str] = None
    raw_material: Optional[dict] = None


# ============ PRODUCTION OUTPUT SCHEMAS ============

class ProductionOutputBase(BaseSchema):
    finished_product_id: UUID
    quantity_produced: Decimal = Field(..., gt=0)
    notes: Optional[str] = None


class ProductionOutputCreate(ProductionOutputBase):
    @field_validator('quantity_produced')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Miqdor musbat bo\'lishi kerak')
        return v


class ProductionOutputResponse(BaseIDSchema):
    shift_id: UUID
    finished_product_id: UUID
    quantity_produced: Decimal
    produced_at: datetime
    notes: Optional[str] = None
    finished_product: Optional[FinishedProductResponse] = None


# ============ DEFECT REASON SCHEMAS ============

class DefectReasonBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class DefectReasonCreate(DefectReasonBase):
    pass


class DefectReasonUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class DefectReasonResponse(BaseIDSchema, DefectReasonBase):
    pass


# ============ DEFECTIVE PRODUCT SCHEMAS ============

class DefectiveProductBase(BaseSchema):
    finished_product_id: UUID
    defect_reason_id: UUID
    quantity: Decimal = Field(..., gt=0)
    notes: Optional[str] = None


class DefectiveProductCreate(DefectiveProductBase):
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Miqdor musbat bo\'lishi kerak')
        return v


class DefectiveProductResponse(BaseIDSchema):
    shift_id: UUID
    finished_product_id: UUID
    defect_reason_id: UUID
    quantity: Decimal
    recorded_at: datetime
    notes: Optional[str] = None
    finished_product: Optional[FinishedProductResponse] = None
    defect_reason: Optional[DefectReasonResponse] = None


# ============ SHIFT HANDOVER SCHEMAS ============

class ShiftHandoverBase(BaseSchema):
    handover_notes: Optional[str] = None
    equipment_status: Optional[str] = None
    pending_issues: Optional[str] = None
    next_shift_instructions: Optional[str] = None


class ShiftHandoverCreate(ShiftHandoverBase):
    pass


class ShiftHandoverResponse(BaseIDSchema, ShiftHandoverBase):
    shift_id: UUID
    handover_time: datetime


# Shift Complete new
class ShiftCompleteRequest(BaseSchema):
    complete_data: ShiftComplete
    handover_data: Optional[ShiftHandoverCreate] = None


# ============ FINISHED PRODUCT STOCK SCHEMAS ============

class FinishedProductStockResponse(BaseIDSchema):
    finished_product_id: UUID
    quantity_total: Decimal
    quantity_available: Decimal
    quantity_reserved: Decimal
    last_updated: datetime
    finished_product: Optional[FinishedProductResponse] = None


# ============ STATISTICS SCHEMAS ============

class ShiftStatistics(BaseSchema):
    shift_id: UUID
    total_raw_materials_used: Decimal
    total_production_output: Decimal
    total_defects: Decimal
    efficiency_percentage: Decimal
    defect_rate_percentage: Decimal


class ProductionLinePerformance(BaseSchema):
    production_line_id: UUID
    production_line_name: str
    total_shifts: int
    total_output: Decimal
    total_defects: Decimal
    average_efficiency: Decimal
    average_defect_rate: Decimal


class ProductionStatistics(BaseSchema):
    total_production_lines: int
    total_machines: int
    active_shifts: int
    completed_shifts_today: int
    total_output_today: Decimal
    total_defects_today: Decimal
    average_efficiency_today: Decimal


# ============ SHIFT PAUSE SCHEMAS ============

class ShiftPauseCreate(BaseSchema):
    reason: str  # breakdown, lunch, other
    notes: Optional[str] = None


class ShiftPauseResponse(BaseIDSchema):
    shift_id: UUID
    paused_at: datetime
    resumed_at: Optional[datetime] = None
    reason: str
    notes: Optional[str] = None

    @property
    def duration_minutes(self) -> Optional[int]:
        if self.paused_at and self.resumed_at:
            return int((self.resumed_at - self.paused_at).total_seconds() / 60)
        return None


# ============ SCRAP STOCK SCHEMAS ============

class ScrapStockResponse(BaseIDSchema):
    finished_product_id: Optional[UUID] = None  # brak uchun
    raw_material_id: Optional[UUID] = None  # recycled uchun
    stock_type: str  # 'brak' | 'recycled'
    quantity: Decimal
    last_updated: datetime
    finished_product: Optional[FinishedProductResponse] = None
    # raw_material inline (import aylanmaslik uchun dict sifatida)
    raw_material: Optional[dict] = None


class ScrapStockTransactionResponse(BaseIDSchema):
    finished_product_id: Optional[UUID] = None
    raw_material_id: Optional[UUID] = None
    transaction_type: str  # brak_in, brak_out, recycled_in, recycled_out
    stock_type: str  # 'brak' | 'recycled'
    quantity: Decimal
    shift_id: Optional[UUID] = None
    notes: Optional[str] = None
    recorded_at: datetime
    finished_product: Optional[FinishedProductResponse] = None
    raw_material: Optional[dict] = None


class ScrapTransferCreate(BaseSchema):
    """Atxotni tegirmonga o'tkazish.

    Kirish: brak (FinishedProduct) → tegirmon → Chiqish: recycled (RawMaterial)
    Chiqish mahsulot asosiy ombor ga TUSHMAYDI — atxot skladda recycled sifatida saqlanadi.
    Operator chiqadigan miqdorni o'zi yozadi, tizim hisoblamaydi.
    """
    # Kirish: brak tayyor mahsulot (PVC quvur, kg)
    input_product_id: UUID  # FinishedProduct.id
    input_quantity: Decimal
    # Chiqish: xom ashyo (PVC granula, kg) — RawMaterial dan tanlanadi
    output_raw_material_id: UUID  # RawMaterial.id — asosiy ombor GA EMAS
    output_quantity: Decimal  # operator yozadi
    notes: Optional[str] = None


# ============ SHIFT SCRAP USAGE SCHEMAS ============

class ShiftScrapUsageCreate(BaseSchema):
    # brak uchun
    finished_product_id: Optional[UUID] = None
    # recycled uchun (raw material — asosiy ombor GA EMAS)
    raw_material_id: Optional[UUID] = None
    quantity_used: Decimal
    stock_type: str = 'recycled'  # 'brak' | 'recycled'
    notes: Optional[str] = None


class ShiftScrapUsageResponse(BaseIDSchema):
    shift_id: UUID
    finished_product_id: UUID
    quantity_used: Decimal
    recorded_at: datetime
    notes: Optional[str] = None
    finished_product: Optional[FinishedProductResponse] = None


# ============ SHIFT CLOSE SCHEMAS (yangilangan) ============

class ShiftOutputItem(BaseSchema):
    """Smena yakunida bitta mahsulot chiqimi"""
    finished_product_id: UUID
    quantity_produced: Decimal
    notes: Optional[str] = None


class ShiftScrapItem(BaseSchema):
    """Smena yakunida bitta atxot yozuvi"""
    finished_product_id: UUID
    quantity: Decimal
    defect_reason_id: Optional[UUID] = None
    notes: Optional[str] = None


class ShiftCloseRequest(BaseSchema):
    """Smena yopish — barcha ma'lumot bir so'rovda"""
    end_time: datetime
    outputs: List[ShiftOutputItem] = []  # ishlab chiqarilgan mahsulotlar
    scraps: List[ShiftScrapItem] = []  # atxot mahsulotlar
    notes: Optional[str] = None
    handover_notes: Optional[str] = None