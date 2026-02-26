from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Date, Integer, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app.models.user import User


class Department(BaseModel):
    """Bo'limlar jadvali"""
    __tablename__ = "departments"

    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Relationships
    employees = relationship("Employee", back_populates="department")

    def __repr__(self):
        return f"<Department {self.name}>"


class Employee(BaseModel):
    """Xodimlar jadvali"""
    __tablename__ = "employees"

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    passport_serial = Column(String(9), nullable=True)
    inn = Column(String(9), nullable=True)

    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id'), nullable=False)
    position = Column(String(100), nullable=False)
    hire_date = Column(Date, nullable=False)
    salary = Column(Numeric(12, 2), nullable=False)
    employment_status = Column(String(20), nullable=False, default='active')  # active, on_leave, terminated

    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)  # Agar user bo'lsa

    # Relationships
    department = relationship("Department", back_populates="employees")
    user = relationship("User")
    attendances = relationship("Attendance", back_populates="employee")
    salaries = relationship("SalaryPayment", back_populates="employee")
    leaves = relationship("LeaveRequest", back_populates="employee")

    def __repr__(self):
        return f"<Employee {self.first_name} {self.last_name}>"


class Attendance(BaseModel):
    """Davomat jadvali"""
    __tablename__ = "attendances"

    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    attendance_date = Column(Date, nullable=False)
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default='present')  # present, absent, late, half_day, on_leave
    notes = Column(Text, nullable=True)

    # Relationships
    employee = relationship("Employee", back_populates="attendances")

    def __repr__(self):
        return f"<Attendance {self.employee_id} - {self.attendance_date}>"


class SalaryPayment(BaseModel):
    """Ish haqi to'lovlari jadvali"""
    __tablename__ = "salary_payments"

    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    payment_date = Column(Date, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    base_salary = Column(Numeric(12, 2), nullable=False)
    bonus = Column(Numeric(12, 2), nullable=False, default=0)
    deductions = Column(Numeric(12, 2), nullable=False, default=0)
    total_amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)  # cash, transfer
    notes = Column(Text, nullable=True)

    # Foreign Keys
    paid_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="salaries")
    payer = relationship("User", foreign_keys=[paid_by])

    def __repr__(self):
        return f"<SalaryPayment {self.employee_id} - {self.payment_date}>"


class LeaveRequest(BaseModel):
    """Ta'til so'rovlari jadvali"""
    __tablename__ = "leave_requests"

    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    leave_type = Column(String(50), nullable=False)  # annual, sick, unpaid, maternity, other
    is_paid = Column(Boolean, default=False, nullable=False)  # True=pullik, False=pulsiz
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_count = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='pending')  # pending, approved, rejected

    # Foreign Keys
    approved_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    # Relationships
    employee = relationship("Employee", back_populates="leaves")
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<LeaveRequest {self.employee_id} - {self.start_date}>"