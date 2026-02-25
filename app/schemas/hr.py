from typing import Optional, List
from pydantic import Field, EmailStr, field_validator
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from app.schemas.base import BaseSchema, BaseIDSchema


# ============ DEPARTMENT SCHEMAS ============

class DepartmentBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class DepartmentResponse(BaseIDSchema, DepartmentBase):
    employee_count: Optional[int] = 0


# ============ EMPLOYEE SCHEMAS ============

class EmployeeBase(BaseSchema):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=9, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    passport_serial: Optional[str] = Field(None, min_length=9, max_length=9)
    inn: Optional[str] = Field(None, min_length=9, max_length=9)
    department_id: UUID
    position: str = Field(..., min_length=1, max_length=100)
    hire_date: date
    salary: Decimal = Field(..., gt=0)
    employment_status: str = Field(default="active", pattern="^(active|on_leave|terminated)$")
    user_id: Optional[UUID] = None


class EmployeeCreate(EmployeeBase):
    @field_validator('salary')
    @classmethod
    def validate_salary(cls, v):
        if v <= 0:
            raise ValueError('Ish haqi musbat bo\'lishi kerak')
        return v


class EmployeeUpdate(BaseSchema):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, min_length=9, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    passport_serial: Optional[str] = Field(None, min_length=9, max_length=9)
    inn: Optional[str] = Field(None, min_length=9, max_length=9)
    department_id: Optional[UUID] = None
    position: Optional[str] = Field(None, min_length=1, max_length=100)
    salary: Optional[Decimal] = Field(None, gt=0)
    employment_status: Optional[str] = Field(None, pattern="^(active|on_leave|terminated)$")


class EmployeeResponse(BaseIDSchema, EmployeeBase):
    department: Optional[DepartmentResponse] = None
    user: Optional[dict] = None


# ============ ATTENDANCE SCHEMAS ============

class AttendanceBase(BaseSchema):
    employee_id: UUID
    attendance_date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: str = Field(default="present", pattern="^(present|absent|late|half_day|on_leave)$")
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseSchema):
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(present|absent|late|half_day|on_leave)$")
    notes: Optional[str] = None


class AttendanceResponse(BaseIDSchema, AttendanceBase):
    employee: Optional[EmployeeResponse] = None


# ============ SALARY PAYMENT SCHEMAS ============

class SalaryPaymentBase(BaseSchema):
    employee_id: UUID
    payment_date: date
    period_start: date
    period_end: date
    base_salary: Decimal = Field(..., gt=0)
    bonus: Decimal = Field(default=Decimal("0"), ge=0)
    deductions: Decimal = Field(default=Decimal("0"), ge=0)
    payment_method: str = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = None


class SalaryPaymentCreate(SalaryPaymentBase):
    @field_validator('base_salary', 'bonus', 'deductions')
    @classmethod
    def validate_amounts(cls, v):
        if v < 0:
            raise ValueError('Summa manfiy bo\'lishi mumkin emas')
        return v


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

class SalaryPaymentResponse(BaseIDSchema):
    employee_id: UUID
    payment_date: date
    period_start: date
    period_end: date
    base_salary: Decimal
    bonus: Decimal
    deductions: Decimal
    total_amount: Decimal
    payment_method: str
    notes: Optional[str] = None
    paid_by: UUID
    employee: Optional[EmployeeResponse] = None
    payer: Optional[CreatorInfo] = None  # ← dict emas

    model_config = {"from_attributes": True}


# ============ LEAVE REQUEST SCHEMAS ============

class LeaveRequestBase(BaseSchema):
    leave_type: str = Field(..., pattern="^(annual|sick|unpaid|maternity)$")
    start_date: date
    end_date: date
    reason: Optional[str] = None


class LeaveRequestCreate(LeaveRequestBase):
    employee_id: UUID


class LeaveRequestUpdate(BaseSchema):
    status: str = Field(..., pattern="^(approved|rejected)$")


class LeaveRequestResponse(BaseIDSchema):
    employee_id: UUID
    leave_type: str
    start_date: date
    end_date: date
    days_count: int
    reason: Optional[str] = None
    status: str
    approved_by: Optional[UUID] = None
    employee: Optional[EmployeeResponse] = None
    approver: Optional[dict] = None


# ============ STATISTICS SCHEMAS ============

class HRStatistics(BaseSchema):
    total_employees: int
    active_employees: int
    total_departments: int
    total_attendance_today: int
    present_today: int
    absent_today: int
    on_leave_today: int
    pending_leave_requests: int
    total_salary_paid_this_month: Decimal