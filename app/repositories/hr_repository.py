from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc
from datetime import date, datetime
from decimal import Decimal
from app.utils.datetime_utils import get_today_start, get_month_start
from uuid import UUID
from app.models.hr import Department, Employee, Attendance, SalaryPayment, LeaveRequest
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, db: Session):
        super().__init__(Department, db)
    
    def get_by_name(self, name: str) -> Optional[Department]:
        """Nom bo'yicha bo'lim topish"""
        return self.db.query(Department).filter(
            Department.name == name,
            Department.is_active == True
        ).first()
    
    def get_with_employee_count(self, department_id: UUID) -> Optional[dict]:
        """Bo'lim va xodimlar soni"""
        department = self.get_by_id(department_id)
        if not department:
            return None
        
        employee_count = self.db.query(func.count(Employee.id)).filter(
            Employee.department_id == department_id,
            Employee.is_active == True
        ).scalar()
        
        return {
            "department": department,
            "employee_count": employee_count
        }


class EmployeeRepository(BaseRepository[Employee]):
    def __init__(self, db: Session):
        super().__init__(Employee, db)
    
    def get_with_relations(self, employee_id: UUID) -> Optional[Employee]:
        """Relationships bilan xodim"""
        return self.db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.user)
        ).filter(
            Employee.id == employee_id,
            Employee.is_active == True
        ).first()
    
    def get_all_with_relations(
        self,
        skip: int = 0,
        limit: int = 100,
        department_id: Optional[UUID] = None,
        employment_status: Optional[str] = None
    ) -> List[Employee]:
        """Barcha xodimlar"""
        query = self.db.query(Employee).options(
            joinedload(Employee.department)
        ).filter(Employee.is_active == True)
        
        if department_id:
            query = query.filter(Employee.department_id == department_id)
        
        if employment_status:
            query = query.filter(Employee.employment_status == employment_status)
        
        return query.order_by(Employee.last_name, Employee.first_name).offset(skip).limit(limit).all()
    
    def get_by_phone(self, phone: str) -> Optional[Employee]:
        """Telefon bo'yicha xodim"""
        return self.db.query(Employee).filter(
            Employee.phone == phone,
            Employee.is_active == True
        ).first()
    
    def get_active_count(self) -> int:
        """Faol xodimlar soni"""
        return self.db.query(func.count(Employee.id)).filter(
            Employee.employment_status == 'active',
            Employee.is_active == True
        ).scalar()


class AttendanceRepository(BaseRepository[Attendance]):
    def __init__(self, db: Session):
        super().__init__(Attendance, db)
    
    def get_by_employee_and_date(self, employee_id: UUID, attendance_date: date) -> Optional[Attendance]:
        """Xodim va sana bo'yicha davomat"""
        return self.db.query(Attendance).filter(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date == attendance_date,
            Attendance.is_active == True
        ).first()
    
    def get_by_employee(
        self,
        employee_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Attendance]:
        """Xodim davomati"""
        query = self.db.query(Attendance).filter(
            Attendance.employee_id == employee_id,
            Attendance.is_active == True
        )
        
        if start_date:
            query = query.filter(Attendance.attendance_date >= start_date)
        
        if end_date:
            query = query.filter(Attendance.attendance_date <= end_date)
        
        return query.order_by(desc(Attendance.attendance_date)).all()
    
    def get_today_attendance(self, attendance_date: date) -> List[Attendance]:
        """Bugungi davomat"""
        return self.db.query(Attendance).options(
            joinedload(Attendance.employee)
        ).filter(
            Attendance.attendance_date == attendance_date,
            Attendance.is_active == True
        ).all()
    
    def get_count_by_status(self, attendance_date: date, status: str) -> int:
        """Status bo'yicha davomat soni"""
        return self.db.query(func.count(Attendance.id)).filter(
            Attendance.attendance_date == attendance_date,
            Attendance.status == status,
            Attendance.is_active == True
        ).scalar()


class SalaryPaymentRepository(BaseRepository[SalaryPayment]):
    def __init__(self, db: Session):
        super().__init__(SalaryPayment, db)
    
    def get_with_relations(self, payment_id: UUID) -> Optional[SalaryPayment]:
        """Relationships bilan to'lov"""
        return self.db.query(SalaryPayment).options(
            joinedload(SalaryPayment.employee).joinedload(Employee.department),
            joinedload(SalaryPayment.payer)
        ).filter(
            SalaryPayment.id == payment_id,
            SalaryPayment.is_active == True
        ).first()
    
    def get_by_employee(
        self,
        employee_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[SalaryPayment]:
        """Xodim to'lovlari"""
        return self.db.query(SalaryPayment).filter(
            SalaryPayment.employee_id == employee_id,
            SalaryPayment.is_active == True
        ).order_by(desc(SalaryPayment.payment_date)).offset(skip).limit(limit).all()
    
    def get_total_paid_this_month(self) -> Decimal:
        """Shu oy to'langan ish haqi"""
        month_start = get_month_start().date()
        
        result = self.db.query(func.sum(SalaryPayment.total_amount)).filter(
            SalaryPayment.payment_date >= month_start,
            SalaryPayment.is_active == True
        ).scalar()
        
        return result or Decimal("0")


class LeaveRequestRepository(BaseRepository[LeaveRequest]):
    def __init__(self, db: Session):
        super().__init__(LeaveRequest, db)
    
    def get_with_relations(self, request_id: UUID) -> Optional[LeaveRequest]:
        """Relationships bilan so'rov"""
        return self.db.query(LeaveRequest).options(
            joinedload(LeaveRequest.employee).joinedload(Employee.department),
            joinedload(LeaveRequest.approver)
        ).filter(
            LeaveRequest.id == request_id,
            LeaveRequest.is_active == True
        ).first()
    
    def get_by_employee(
        self,
        employee_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[LeaveRequest]:
        """Xodim ta'til so'rovlari"""
        return self.db.query(LeaveRequest).filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.is_active == True
        ).order_by(desc(LeaveRequest.created_at)).offset(skip).limit(limit).all()
    
    def get_all_with_relations(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[LeaveRequest]:
        """Barcha so'rovlar"""
        query = self.db.query(LeaveRequest).options(
            joinedload(LeaveRequest.employee)
        ).filter(LeaveRequest.is_active == True)
        
        if status:
            query = query.filter(LeaveRequest.status == status)
        
        return query.order_by(desc(LeaveRequest.created_at)).offset(skip).limit(limit).all()
    
    def get_pending_count(self) -> int:
        """Kutilayotgan so'rovlar soni"""
        return self.db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.status == 'pending',
            LeaveRequest.is_active == True
        ).scalar()
    
    def get_on_leave_today(self, today: date) -> int:
        """Bugun ta'tilda bo'lganlar soni"""
        return self.db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today,
            LeaveRequest.is_active == True
        ).scalar()