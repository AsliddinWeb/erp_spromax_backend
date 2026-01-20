from typing import Optional, List
from pydantic import Field, field_validator
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from app.schemas.base import BaseSchema, BaseIDSchema
from app.core.constants import RequestStatus


# ============ SUPPLIER SCHEMAS ============

class SupplierBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: str = Field(..., min_length=9, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    inn: Optional[str] = Field(None, min_length=9, max_length=9)
    
    @field_validator('inn')
    @classmethod
    def validate_inn(cls, v):
        if v and not v.isdigit():
            raise ValueError('INN faqat raqamlardan iborat bo\'lishi kerak')
        return v


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, min_length=9, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    inn: Optional[str] = Field(None, min_length=9, max_length=9)


class SupplierResponse(BaseIDSchema, SupplierBase):
    pass


# ============ RAW MATERIAL SCHEMAS ============

class RawMaterialBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    unit: str = Field(..., min_length=1, max_length=20)
    minimum_stock: Decimal = Field(default=Decimal("0"), ge=0)


class RawMaterialCreate(RawMaterialBase):
    pass


class RawMaterialUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    minimum_stock: Optional[Decimal] = Field(None, ge=0)


class RawMaterialResponse(BaseIDSchema, RawMaterialBase):
    current_stock: Optional[Decimal] = None


# ============ WAREHOUSE RECEIPT SCHEMAS ============

class WarehouseReceiptBase(BaseSchema):
    supplier_id: UUID
    raw_material_id: UUID
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)
    receipt_date: datetime
    notes: Optional[str] = None


class WarehouseReceiptCreate(WarehouseReceiptBase):
    @field_validator('quantity', 'unit_price')
    @classmethod
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError('Qiymat musbat bo\'lishi kerak')
        return v


class WarehouseReceiptResponse(BaseIDSchema, WarehouseReceiptBase):
    batch_number: str
    total_price: Decimal
    supplier: Optional[SupplierResponse] = None
    raw_material: Optional[RawMaterialResponse] = None


# ============ WAREHOUSE STOCK SCHEMAS ============

class WarehouseStockResponse(BaseIDSchema):
    raw_material_id: UUID
    quantity: Decimal
    last_updated: datetime
    raw_material: Optional[RawMaterialResponse] = None


class LowStockItem(BaseSchema):
    raw_material_id: UUID
    raw_material_name: str
    current_stock: Decimal
    minimum_stock: Decimal
    difference: Decimal
    unit: str


# ============ MATERIAL REQUEST SCHEMAS ============

class MaterialRequestBase(BaseSchema):
    raw_material_id: UUID
    requested_quantity: Decimal = Field(..., gt=0)
    notes: Optional[str] = None


class MaterialRequestCreate(MaterialRequestBase):
    @field_validator('requested_quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Miqdor musbat bo\'lishi kerak')
        return v


class MaterialRequestApprove(BaseSchema):
    approved_quantity: Decimal = Field(..., gt=0)
    notes: Optional[str] = None


class MaterialRequestReject(BaseSchema):
    rejection_reason: str = Field(..., min_length=1)


class MaterialRequestResponse(BaseIDSchema):
    raw_material_id: UUID
    requested_quantity: Decimal
    approved_quantity: Optional[Decimal] = None
    request_status: str
    requested_by: UUID
    approved_by: Optional[UUID] = None
    request_date: datetime
    approval_date: Optional[datetime] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    raw_material: Optional[RawMaterialResponse] = None
    requester: Optional[dict] = None
    approver: Optional[dict] = None


# ============ STATISTICS SCHEMAS ============

class WarehouseStatistics(BaseSchema):
    total_suppliers: int
    total_raw_materials: int
    total_stock_value: Decimal
    low_stock_items_count: int
    pending_requests_count: int
    total_receipts_this_month: int
    total_receipts_value_this_month: Decimal