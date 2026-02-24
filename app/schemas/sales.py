from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, EmailStr, field_validator, ConfigDict, BaseModel

from app.schemas.base import BaseSchema, BaseIDSchema


# ================= USER SHORT =================

class UserShort(BaseModel):
    id: UUID
    username: str

    model_config = ConfigDict(from_attributes=True)


# ================= CUSTOMER =================

class CustomerBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: str = Field(..., min_length=9, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    inn: Optional[str] = Field(None, min_length=9, max_length=9)
    customer_type: str = Field(default="regular", pattern="^(regular|wholesale|vip)$")

    @field_validator('inn')
    @classmethod
    def validate_inn(cls, v):
        if v and not v.isdigit():
            raise ValueError("INN faqat raqamlardan iborat bo‘lishi kerak")
        return v


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, min_length=9, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    inn: Optional[str] = Field(None, min_length=9, max_length=9)
    customer_type: Optional[str] = Field(None, pattern="^(regular|wholesale|vip)$")


class CustomerResponse(BaseIDSchema, CustomerBase):
    total_orders: Optional[int] = 0
    total_spent: Optional[Decimal] = Decimal("0")

    model_config = ConfigDict(from_attributes=True)


# ================= ORDER ITEMS =================

class OrderItemBase(BaseSchema):
    finished_product_id: UUID
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)


class OrderItemCreate(OrderItemBase):
    @field_validator('quantity', 'unit_price')
    @classmethod
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError("Qiymat musbat bo‘lishi kerak")
        return v


class OrderItemResponse(BaseIDSchema):
    order_id: UUID
    finished_product_id: UUID
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    finished_product: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


# ================= ORDERS =================

class OrderBase(BaseSchema):
    customer_id: UUID
    order_date: datetime
    delivery_address: Optional[str] = None
    delivery_date: Optional[datetime] = None
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderUpdate(BaseSchema):
    delivery_address: Optional[str] = None
    delivery_date: Optional[datetime] = None
    delivery_status: Optional[str] = Field(None, pattern="^(pending|processing|shipped|delivered|cancelled)$")
    notes: Optional[str] = None


class OrderResponse(BaseIDSchema):
    customer_id: UUID
    order_date: datetime
    total_amount: Decimal
    paid_amount: Decimal
    payment_status: str
    delivery_status: str
    delivery_address: Optional[str] = None
    delivery_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_by: UUID

    customer: Optional[CustomerResponse] = None
    creator: Optional[UserShort] = None

    order_items: List[OrderItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @property
    def remaining_amount(self) -> Decimal:
        return self.total_amount - self.paid_amount


# ================= PAYMENTS =================

class PaymentBase(BaseSchema):
    amount: Decimal = Field(..., gt=0)
    payment_date: datetime
    payment_method: str = Field(..., min_length=1, max_length=50)
    transaction_id: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    order_id: UUID

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("To‘lov summasi musbat bo‘lishi kerak")
        return v


class PaymentResponse(BaseIDSchema, PaymentBase):
    order_id: UUID
    received_by: UUID
    receiver: Optional[UserShort] = None

    model_config = ConfigDict(from_attributes=True)


# ================= STATISTICS =================

class SalesStatistics(BaseSchema):
    total_customers: int
    total_orders: int
    total_revenue: Decimal
    total_paid: Decimal
    total_unpaid: Decimal
    pending_orders: int
    completed_orders_today: int
    revenue_today: Decimal

    top_customers: List[dict] = Field(default_factory=list)
    top_products: List[dict] = Field(default_factory=list)


class CustomerStatistics(BaseSchema):
    customer_id: UUID
    customer_name: str
    total_orders: int
    total_spent: Decimal
    total_paid: Decimal
    total_unpaid: Decimal
    last_order_date: Optional[datetime] = None