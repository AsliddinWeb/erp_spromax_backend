from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID
from calendar import monthrange
from app.models.hr import Department, Employee, Attendance, SalaryPayment, LeaveRequest
from app.schemas.hr import (
    DepartmentCreate,
    DepartmentUpdate,
    EmployeeCreate,
    EmployeeUpdate,
    AttendanceCreate,
    AttendanceUpdate,
    SalaryPaymentCreate,
    LeaveRequestCreate,
    LeaveRequestUpdate,
    HRStatistics,
    SalaryPreviewItem,
    BatchSalaryPaymentCreate,
    BatchSalaryPaymentResponse,
)
from app.repositories.hr_repository import (
    DepartmentRepository,
    EmployeeRepository,
    AttendanceRepository,
    SalaryPaymentRepository,
    LeaveRequestRepository
)
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException
)


class HRService:
    def __init__(self, db: Session):
        self.db = db
        self.department_repo = DepartmentRepository(db)
        self.employee_repo = EmployeeRepository(db)
        self.attendance_repo = AttendanceRepository(db)
        self.salary_repo = SalaryPaymentRepository(db)
        self.leave_repo = LeaveRequestRepository(db)

    # ============ DEPARTMENT METHODS ============

    def create_department(self, department_data: DepartmentCreate) -> Department:
        """Yangi bo'lim yaratish"""
        existing = self.department_repo.get_by_name(department_data.name)
        if existing:
            raise ConflictException(detail=f"'{department_data.name}' nomli bo'lim mavjud")

        new_department = Department(**department_data.model_dump())
        return self.department_repo.create(new_department)

    def get_department(self, department_id: UUID) -> Department:
        """Bo'lim olish"""
        department = self.department_repo.get_by_id(department_id)
        if not department:
            raise NotFoundException(detail="Bo'lim topilmadi")
        return department

    def get_all_departments(self, skip: int = 0, limit: int = 100) -> List[Department]:
        """Barcha bo'limlar"""
        departments = self.department_repo.get_all(skip=skip, limit=limit)
        for dept in departments:
            dept.employee_count = self.db.query(Employee).filter(
                Employee.department_id == dept.id,
                Employee.is_active == True
            ).count()
        return departments

    def update_department(self, department_id: UUID, department_data: DepartmentUpdate) -> Department:
        """Bo'lim yangilash"""
        department = self.get_department(department_id)

        if department_data.name and department_data.name != department.name:
            existing = self.department_repo.get_by_name(department_data.name)
            if existing:
                raise ConflictException(detail=f"'{department_data.name}' nomli bo'lim mavjud")

        update_data = department_data.model_dump(exclude_unset=True)
        return self.department_repo.update(department, update_data)

    def delete_department(self, department_id: UUID) -> bool:
        """Bo'lim o'chirish"""
        return self.department_repo.delete(department_id)

    # ============ EMPLOYEE METHODS ============

    def create_employee(self, employee_data: EmployeeCreate) -> Employee:
        """Yangi xodim yaratish"""
        # Bo'lim tekshirish
        department = self.get_department(employee_data.department_id)

        # Telefon tekshirish
        existing = self.employee_repo.get_by_phone(employee_data.phone)
        if existing:
            raise ConflictException(detail=f"'{employee_data.phone}' telefon raqami bilan xodim mavjud")

        new_employee = Employee(**employee_data.model_dump())
        return self.employee_repo.create(new_employee)

    def get_employee(self, employee_id: UUID) -> Employee:
        """Xodim olish"""
        employee = self.employee_repo.get_with_relations(employee_id)
        if not employee:
            raise NotFoundException(detail="Xodim topilmadi")
        return employee

    def get_all_employees(
            self,
            skip: int = 0,
            limit: int = 100,
            department_id: Optional[UUID] = None,
            employment_status: Optional[str] = None
    ) -> List[Employee]:
        """Barcha xodimlar"""
        return self.employee_repo.get_all_with_relations(
            skip=skip,
            limit=limit,
            department_id=department_id,
            employment_status=employment_status
        )

    def update_employee(self, employee_id: UUID, employee_data: EmployeeUpdate) -> Employee:
        """Xodim yangilash"""
        employee = self.get_employee(employee_id)

        if employee_data.phone and employee_data.phone != employee.phone:
            existing = self.employee_repo.get_by_phone(employee_data.phone)
            if existing:
                raise ConflictException(detail=f"'{employee_data.phone}' telefon raqami bilan xodim mavjud")

        update_data = employee_data.model_dump(exclude_unset=True)
        return self.employee_repo.update(employee, update_data)

    def delete_employee(self, employee_id: UUID) -> bool:
        """Xodim o'chirish"""
        return self.employee_repo.delete(employee_id)

    # ============ ATTENDANCE METHODS ============

    def get_all_attendances(self, skip: int = 0, limit: int = 100) -> List[Attendance]:
        """Barcha davomatlar"""
        return self.db.query(Attendance).order_by(
            Attendance.attendance_date.desc()
        ).offset(skip).limit(limit).all()

    def create_attendance(self, attendance_data: AttendanceCreate) -> Attendance:
        """Davomat yozish"""
        # Xodim tekshirish
        employee = self.get_employee(attendance_data.employee_id)

        # Shu kunlik davomat borligini tekshirish
        existing = self.attendance_repo.get_by_employee_and_date(
            attendance_data.employee_id,
            attendance_data.attendance_date
        )
        if existing:
            raise ConflictException(detail="Shu kun uchun davomat allaqachon yozilgan")

        new_attendance = Attendance(**attendance_data.model_dump())
        return self.attendance_repo.create(new_attendance)

    def get_attendance(self, attendance_id: UUID) -> Attendance:
        """Davomat olish"""
        attendance = self.attendance_repo.get_by_id(attendance_id)
        if not attendance:
            raise NotFoundException(detail="Davomat topilmadi")
        return attendance

    def get_employee_attendance(
            self,
            employee_id: UUID,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> List[Attendance]:
        """Xodim davomati"""
        return self.attendance_repo.get_by_employee(employee_id, start_date, end_date)

    def get_today_attendance(self, attendance_date: date) -> List[Attendance]:
        """Bugungi davomat"""
        return self.attendance_repo.get_today_attendance(attendance_date)

    def update_attendance(self, attendance_id: UUID, attendance_data: AttendanceUpdate) -> Attendance:
        """Davomat yangilash"""
        attendance = self.get_attendance(attendance_id)
        update_data = attendance_data.model_dump(exclude_unset=True)
        return self.attendance_repo.update(attendance, update_data)

    def delete_attendance(self, attendance_id: UUID) -> bool:
        """Davomat o'chirish"""
        return self.attendance_repo.delete(attendance_id)

    # ============ SALARY PAYMENT METHODS ============

    def create_salary_payment(
            self,
            payment_data: SalaryPaymentCreate,
            user_id: UUID
    ) -> SalaryPayment:
        """Ish haqi to'lovi"""
        # Xodim tekshirish
        employee = self.get_employee(payment_data.employee_id)

        # Total amount hisoblash
        total_amount = payment_data.base_salary + payment_data.bonus - payment_data.deductions

        new_payment = SalaryPayment(
            employee_id=payment_data.employee_id,
            payment_date=payment_data.payment_date,
            period_start=payment_data.period_start,
            period_end=payment_data.period_end,
            base_salary=payment_data.base_salary,
            bonus=payment_data.bonus,
            deductions=payment_data.deductions,
            total_amount=total_amount,
            payment_method=payment_data.payment_method,
            notes=payment_data.notes,
            paid_by=user_id
        )

        salary_payment = self.salary_repo.create(new_payment)

        # ✅ Moliya — avtomatik tranzaksiya yaratish
        try:
            from app.services.finance_service import FinanceService
            finance_service = FinanceService(self.db)
            full_name = f"{employee.first_name} {employee.last_name}"
            finance_service.create_automatic_transaction(
                transaction_type="expense",
                amount=total_amount,
                category_name="Ish haqi xarajatlari",
                description=f"Ish haqi — {full_name}",
                reference_type="salary_payment",
                reference_id=salary_payment.id,
                user_id=user_id
            )
        except Exception:
            pass  # Moliya xatosi asosiy to'lovni bloklamasin

        return salary_payment

    # ============ BATCH SALARY METHODS ============

    def calculate_salary_preview(self, month: str) -> List[SalaryPreviewItem]:
        """Oy uchun barcha xodimlar oylik hisob-kitobi preview"""
        # "2026-02" → year=2026, month=2
        year, mon = int(month.split("-")[0]), int(month.split("-")[1])
        period_start = date(year, mon, 1)
        period_end = date(year, mon, monthrange(year, mon)[1])

        # Faqat active xodimlar
        employees = self.db.query(Employee).filter(
            Employee.employment_status == 'active',
            Employee.is_active == True
        ).all()

        result = []
        for emp in employees:
            daily_salary = (emp.salary / Decimal("26")).quantize(Decimal("1"))

            # Shu oyda approved + is_paid=False ta'tillar
            unpaid_leaves = self.db.query(LeaveRequest).filter(
                LeaveRequest.employee_id == emp.id,
                LeaveRequest.status == 'approved',
                LeaveRequest.is_paid == False,
                LeaveRequest.start_date >= period_start,
                LeaveRequest.start_date <= period_end,
                LeaveRequest.is_active == True
            ).all()

            unpaid_days = sum(lr.days_count for lr in unpaid_leaves)
            deduction = (daily_salary * unpaid_days).quantize(Decimal("1"))
            total = (emp.salary - deduction).quantize(Decimal("1"))

            dept_name = emp.department.name if emp.department else "—"

            result.append(SalaryPreviewItem(
                employee_id=emp.id,
                full_name=f"{emp.first_name} {emp.last_name}",
                department=dept_name,
                base_salary=emp.salary,
                unpaid_leave_days=unpaid_days,
                daily_salary=daily_salary,
                deduction=deduction,
                bonus=Decimal("0"),
                total_amount=total
            ))

        return result

    def batch_salary_payment(
            self,
            batch_data: BatchSalaryPaymentCreate,
            user_id: UUID
    ) -> BatchSalaryPaymentResponse:
        """Batch oylik to'lovi"""
        year, mon = int(batch_data.month.split("-")[0]), int(batch_data.month.split("-")[1])
        period_start = date(year, mon, 1)
        period_end = date(year, mon, monthrange(year, mon)[1])
        today = date.today()

        success_count = 0
        failed_count = 0
        total_amount = Decimal("0")
        errors = []

        for item in batch_data.payments:
            try:
                # Allaqachon to'langan bo'lsa tekshirish
                existing = self.db.query(SalaryPayment).filter(
                    SalaryPayment.employee_id == item.employee_id,
                    SalaryPayment.period_start == period_start,
                    SalaryPayment.period_end == period_end,
                    SalaryPayment.is_active == True
                ).first()

                if existing:
                    employee = self.db.query(Employee).filter(
                        Employee.id == item.employee_id
                    ).first()
                    name = f"{employee.first_name} {employee.last_name}" if employee else str(item.employee_id)
                    errors.append(f"{name}: Bu oy uchun ish haqi allaqachon to'langan")
                    failed_count += 1
                    continue

                # Xodim tekshirish
                employee = self.get_employee(item.employee_id)
                computed_total = item.base_salary + item.bonus - item.deduction

                new_payment = SalaryPayment(
                    employee_id=item.employee_id,
                    payment_date=today,
                    period_start=period_start,
                    period_end=period_end,
                    base_salary=item.base_salary,
                    bonus=item.bonus,
                    deductions=item.deduction,
                    total_amount=computed_total,
                    payment_method="bank_transfer",
                    notes=item.notes or f"{batch_data.month} oyi ish haqi",
                    paid_by=user_id
                )
                salary_payment = self.salary_repo.create(new_payment)

                # Finance auto-transaction
                try:
                    from app.services.finance_service import FinanceService
                    finance_service = FinanceService(self.db)
                    full_name = f"{employee.first_name} {employee.last_name}"
                    finance_service.create_automatic_transaction(
                        transaction_type="expense",
                        amount=computed_total,
                        category_name="Ish haqi xarajatlari",
                        description=f"Ish haqi — {full_name} ({batch_data.month})",
                        reference_type="salary_payment",
                        reference_id=salary_payment.id,
                        user_id=user_id
                    )
                except Exception:
                    pass

                success_count += 1
                total_amount += computed_total

            except Exception as e:
                failed_count += 1
                errors.append(f"Xodim {item.employee_id}: {str(e)}")

        return BatchSalaryPaymentResponse(
            success_count=success_count,
            failed_count=failed_count,
            total_amount=total_amount,
            errors=errors
        )

    def get_salary_payment(self, payment_id: UUID) -> SalaryPayment:
        """To'lov olish"""
        payment = self.salary_repo.get_with_relations(payment_id)
        if not payment:
            raise NotFoundException(detail="To'lov topilmadi")
        return payment

    def get_employee_salary_payments(
            self,
            employee_id: UUID,
            skip: int = 0,
            limit: int = 100
    ) -> List[SalaryPayment]:
        """Xodim to'lovlari"""
        return self.salary_repo.get_by_employee(employee_id, skip=skip, limit=limit)

    def get_all_salary_payments(self, skip: int = 0, limit: int = 100) -> List[SalaryPayment]:
        """Barcha ish haqi to'lovlari"""
        return self.db.query(SalaryPayment).order_by(
            SalaryPayment.payment_date.desc()
        ).offset(skip).limit(limit).all()

    # ============ LEAVE REQUEST METHODS ============

    def create_leave_request(self, leave_data: LeaveRequestCreate) -> LeaveRequest:
        """Ta'til so'rovi yaratish"""
        # Xodim tekshirish
        employee = self.get_employee(leave_data.employee_id)

        # Kunlar sonini hisoblash
        days_count = (leave_data.end_date - leave_data.start_date).days + 1

        if days_count <= 0:
            raise BadRequestException(detail="Tugash sanasi boshlanish sanasidan keyin bo'lishi kerak")

        new_request = LeaveRequest(
            employee_id=leave_data.employee_id,
            leave_type=leave_data.leave_type,
            start_date=leave_data.start_date,
            end_date=leave_data.end_date,
            days_count=days_count,
            reason=leave_data.reason,
            status='pending'
        )

        return self.leave_repo.create(new_request)

    def get_leave_request(self, request_id: UUID) -> LeaveRequest:
        """So'rov olish"""
        request = self.leave_repo.get_with_relations(request_id)
        if not request:
            raise NotFoundException(detail="So'rov topilmadi")
        return request

    def get_all_leave_requests(
            self,
            skip: int = 0,
            limit: int = 100,
            status: Optional[str] = None
    ) -> List[LeaveRequest]:
        """Barcha so'rovlar"""
        return self.leave_repo.get_all_with_relations(skip=skip, limit=limit, status=status)

    def get_employee_leave_requests(
            self,
            employee_id: UUID,
            skip: int = 0,
            limit: int = 100
    ) -> List[LeaveRequest]:
        """Xodim so'rovlari"""
        return self.leave_repo.get_by_employee(employee_id, skip=skip, limit=limit)

    def approve_leave_request(
            self,
            request_id: UUID,
            update_data: LeaveRequestUpdate,
            user_id: UUID
    ) -> LeaveRequest:
        """So'rovni tasdiqlash yoki rad etish"""
        leave_request = self.get_leave_request(request_id)

        if leave_request.status != 'pending':
            raise BadRequestException(detail="So'rov allaqachon ko'rib chiqilgan")

        leave_request.status = update_data.status
        leave_request.approved_by = user_id

        self.db.commit()
        self.db.refresh(leave_request)

        return leave_request

    # ============ STATISTICS METHODS ============

    def get_statistics(self) -> HRStatistics:
        """HR statistika"""
        total_employees = self.employee_repo.count()
        active_employees = self.employee_repo.get_active_count()
        total_departments = self.department_repo.count()

        today = date.today()
        total_attendance_today = len(self.attendance_repo.get_today_attendance(today))
        present_today = self.attendance_repo.get_count_by_status(today, 'present')
        absent_today = self.attendance_repo.get_count_by_status(today, 'absent')
        on_leave_today = self.leave_repo.get_on_leave_today(today)

        pending_leave_requests = self.leave_repo.get_pending_count()
        total_salary_paid_this_month = self.salary_repo.get_total_paid_this_month()

        return HRStatistics(
            total_employees=total_employees,
            active_employees=active_employees,
            total_departments=total_departments,
            total_attendance_today=total_attendance_today,
            present_today=present_today,
            absent_today=absent_today,
            on_leave_today=on_leave_today,
            pending_leave_requests=pending_leave_requests,
            total_salary_paid_this_month=total_salary_paid_this_month
        )