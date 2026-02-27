from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from datetime import date
from uuid import UUID
from app.database import get_db
from app.schemas.hr import (
    # Department
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    # Employee
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    # Attendance
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceResponse,
    # Salary
    SalaryPaymentCreate,
    SalaryPaymentResponse,
    SalaryPreviewItem,
    BatchSalaryPaymentCreate,
    BatchSalaryPaymentResponse,
    # Leave
    LeaveRequestCreate,
    LeaveRequestUpdate,
    LeaveRequestResponse,
    # Statistics
    HRStatistics
)
from app.services.hr_service import HRService
from app.dependencies import get_current_user, require_permission
from app.models.user import User
from app.core.constants import PermissionType

router = APIRouter(prefix="/hr", tags=["HR"])


# ============ DEPARTMENT ENDPOINTS ============

@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
        department_data: DepartmentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_HR))
):
    """Yangi bo'lim yaratish"""
    service = HRService(db)
    return service.create_department(department_data)


@router.get("/departments", response_model=List[DepartmentResponse])
async def get_departments(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """Barcha bo'limlar ro'yxati"""
    service = HRService(db)
    return service.get_all_departments(skip=skip, limit=limit)


@router.get("/departments/{department_id}", response_model=DepartmentResponse)
async def get_department(
        department_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """Bitta bo'lim ma'lumotlari"""
    service = HRService(db)
    return service.get_department(department_id)


@router.put("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(
        department_id: UUID,
        department_data: DepartmentUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_HR))
):
    """Bo'lim yangilash"""
    service = HRService(db)
    return service.update_department(department_id, department_data)


@router.delete("/departments/{department_id}", status_code=status.HTTP_200_OK)
async def delete_department(
        department_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_HR))
):
    """Bo'lim o'chirish"""
    service = HRService(db)
    service.delete_department(department_id)
    return {"message": "Bo'lim o'chirildi"}


# ============ EMPLOYEE ENDPOINTS ============

@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
        employee_data: EmployeeCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_HR))
):
    """Yangi xodim qo'shish"""
    service = HRService(db)
    return service.create_employee(employee_data)


@router.get("/employees", response_model=List[EmployeeResponse])
async def get_employees(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        department_id: Optional[UUID] = Query(None),
        employment_status: Optional[str] = Query(None, pattern="^(active|on_leave|terminated)$"),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """
    Xodimlar ro'yxati

    Filtrlash: bo'lim, ish holati
    """
    service = HRService(db)
    return service.get_all_employees(
        skip=skip,
        limit=limit,
        department_id=department_id,
        employment_status=employment_status
    )


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
        employee_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """Bitta xodim ma'lumotlari"""
    service = HRService(db)
    return service.get_employee(employee_id)


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
        employee_id: UUID,
        employee_data: EmployeeUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_HR))
):
    """Xodim ma'lumotlarini yangilash"""
    service = HRService(db)
    return service.update_employee(employee_id, employee_data)


@router.delete("/employees/{employee_id}", status_code=status.HTTP_200_OK)
async def delete_employee(
        employee_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_HR))
):
    """Xodimni o'chirish"""
    service = HRService(db)
    service.delete_employee(employee_id)
    return {"message": "Xodim o'chirildi"}


# ============ ATTENDANCE ENDPOINTS ============

@router.get("/attendances", response_model=List[AttendanceResponse])
async def get_all_attendances(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """Barcha davomatlar"""
    service = HRService(db)
    return service.get_all_attendances(skip=skip, limit=limit)


@router.post("/attendances", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def create_attendance(
        attendance_data: AttendanceCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_HR))
):
    """
    Davomat yozish

    Xodimning kunlik davomatini kiritish.
    """
    service = HRService(db)
    return service.create_attendance(attendance_data)


@router.get("/attendances/today", response_model=List[AttendanceResponse])
async def get_today_attendance(
        attendance_date: date = Query(default_factory=date.today),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """Bugungi davomat"""
    service = HRService(db)
    return service.get_today_attendance(attendance_date)


@router.get("/employees/{employee_id}/attendances", response_model=List[AttendanceResponse])
async def get_employee_attendance(
        employee_id: UUID,
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """Xodim davomati tarixi"""
    service = HRService(db)
    return service.get_employee_attendance(employee_id, start_date, end_date)


@router.put("/attendances/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
        attendance_id: UUID,
        attendance_data: AttendanceUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_HR))
):
    """Davomat yangilash"""
    service = HRService(db)
    return service.update_attendance(attendance_id, attendance_data)


@router.delete("/attendances/{attendance_id}", status_code=status.HTTP_200_OK)
async def delete_attendance(
        attendance_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_HR))
):
    """Davomat o'chirish"""
    service = HRService(db)
    service.delete_attendance(attendance_id)
    return {"message": "Davomat o'chirildi"}


# ============ SALARY PAYMENT ENDPOINTS ============

@router.get("/salary-payments", response_model=List[SalaryPaymentResponse])
async def get_salary_payments(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """Barcha ish haqi to'lovlari"""
    service = HRService(db)
    return service.get_all_salary_payments(skip=skip, limit=limit)


@router.post("/salary-payments", response_model=SalaryPaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_salary_payment(
        payment_data: SalaryPaymentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_HR))
):
    """
    Ish haqi to'lovi

    Xodimga ish haqi to'lash va yozib qo'yish.
    """
    service = HRService(db)
    return service.create_salary_payment(payment_data, current_user.id)


@router.get("/salary-payments/calculate-preview", response_model=List[SalaryPreviewItem])
async def calculate_salary_preview(
        month: str = Query(..., pattern=r"^\d{4}-\d{2}$", description="Format: 2026-02"),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """
    Oylik hisoblash preview

    Barcha active xodimlar uchun shu oyning ish haqi hisobini ko'rsatadi.
    Approved + pulsiz ta'tillar avtomatik chegirma qilinadi.
    """
    service = HRService(db)
    return service.calculate_salary_preview(month)


@router.post("/salary-payments/batch", response_model=BatchSalaryPaymentResponse, status_code=status.HTTP_201_CREATED)
async def batch_salary_payment(
        batch_data: BatchSalaryPaymentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_HR))
):
    """
    Batch oylik to'lovi

    Bir nechta xodimga bir vaqtda ish haqi to'lash.
    Allaqachon to'langan xodimlar uchun xato qaytariladi.
    """
    service = HRService(db)
    return service.batch_salary_payment(batch_data, current_user.id)


@router.get("/salary-payments/{payment_id}", response_model=SalaryPaymentResponse)
async def get_salary_payment(
        payment_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """Bitta to'lov ma'lumotlari"""
    service = HRService(db)
    return service.get_salary_payment(payment_id)


@router.get("/employees/{employee_id}/salary-payments", response_model=List[SalaryPaymentResponse])
async def get_employee_salary_payments(
        employee_id: UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """Xodim ish haqi to'lovlari tarixi"""
    service = HRService(db)
    return service.get_employee_salary_payments(employee_id, skip=skip, limit=limit)


# ============ LEAVE REQUEST ENDPOINTS ============

@router.post("/leave-requests", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_request(
        leave_data: LeaveRequestCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Ta'til so'rovi yaratish

    Xodim ta'til olish uchun so'rov yuboradi.
    """
    service = HRService(db)
    return service.create_leave_request(leave_data)


@router.get("/leave-requests", response_model=List[LeaveRequestResponse])
async def get_leave_requests(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        status: Optional[str] = Query(None, pattern="^(pending|approved|rejected)$"),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """
    Barcha ta'til so'rovlari

    Filtrlash: holat (pending, approved, rejected)
    """
    service = HRService(db)
    return service.get_all_leave_requests(skip=skip, limit=limit, status=status)


@router.get("/leave-requests/{request_id}", response_model=LeaveRequestResponse)
async def get_leave_request(
        request_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Bitta ta'til so'rovi"""
    service = HRService(db)
    return service.get_leave_request(request_id)


@router.get("/employees/{employee_id}/leave-requests", response_model=List[LeaveRequestResponse])
async def get_employee_leave_requests(
        employee_id: UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Xodim ta'til so'rovlari"""
    service = HRService(db)
    return service.get_employee_leave_requests(employee_id, skip=skip, limit=limit)


@router.put("/leave-requests/{request_id}/approve", response_model=LeaveRequestResponse)
async def approve_leave_request(
        request_id: UUID,
        update_data: LeaveRequestUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_HR))
):
    """
    Ta'til so'rovini tasdiqlash/rad etish

    Rahbar so'rovni ko'rib chiqadi va qaror qabul qiladi.
    """
    service = HRService(db)
    return service.approve_leave_request(request_id, update_data, current_user.id)


# ============ STATISTICS ENDPOINT ============

@router.get("/statistics", response_model=HRStatistics)
async def get_statistics(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """HR statistika"""
    service = HRService(db)
    return service.get_statistics()