from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, datetime, timedelta
from decimal import Decimal
from app.schemas.analytics import (
    DashboardOverview,
    SalesAnalytics,
    ProductionAnalytics,
    FinanceAnalytics,
    HRAnalytics,
    InventoryAnalytics,
    MaintenanceAnalytics,
    KPIMetrics,
    ComparisonReport,
    PeriodComparison
)
from app.services.sales_service import SalesService
from app.services.production_service import ProductionService
from app.services.finance_service import FinanceService
from app.services.hr_service import HRService
from app.services.warehouse_service import WarehouseService
from app.services.maintenance_service import MaintenanceService
from app.repositories.sales_repository import CustomerRepository, OrderRepository
from app.repositories.production_repository import (
    ProductionLineRepository,
    ShiftRepository,
    ProductionOutputRepository,
    DefectiveProductRepository
)
from app.repositories.finance_repository import FinancialTransactionRepository
from app.repositories.hr_repository import EmployeeRepository, DepartmentRepository, AttendanceRepository
from app.repositories.warehouse_repository import RawMaterialRepository, WarehouseStockRepository
from app.repositories.production_repository import FinishedProductStockRepository
from app.repositories.maintenance_repository import MaintenanceRequestRepository, SparePartRepository


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        
        # Services
        self.sales_service = SalesService(db)
        self.production_service = ProductionService(db)
        self.finance_service = FinanceService(db)
        self.hr_service = HRService(db)
        self.warehouse_service = WarehouseService(db)
        self.maintenance_service = MaintenanceService(db)
        
        # Repositories
        self.customer_repo = CustomerRepository(db)
        self.order_repo = OrderRepository(db)
        self.production_line_repo = ProductionLineRepository(db)
        self.shift_repo = ShiftRepository(db)
        self.output_repo = ProductionOutputRepository(db)
        self.defect_repo = DefectiveProductRepository(db)
        self.transaction_repo = FinancialTransactionRepository(db)
        self.employee_repo = EmployeeRepository(db)
        self.department_repo = DepartmentRepository(db)
        self.attendance_repo = AttendanceRepository(db)
        self.raw_material_repo = RawMaterialRepository(db)
        self.warehouse_stock_repo = WarehouseStockRepository(db)
        self.finished_stock_repo = FinishedProductStockRepository(db)
        self.maintenance_repo = MaintenanceRequestRepository(db)
        self.spare_part_repo = SparePartRepository(db)
    
    # ============ DASHBOARD METHODS ============
    
    def get_dashboard_overview(self) -> DashboardOverview:
        """Asosiy dashboard ma'lumotlari"""
        # HR
        total_employees = self.employee_repo.count()
        active_employees = self.employee_repo.get_active_count()
        
        # Sales
        total_customers = self.customer_repo.count()
        total_orders = self.order_repo.count()
        pending_orders = self.order_repo.get_pending_count()
        total_revenue = self.order_repo.get_total_revenue()
        revenue_today = self.order_repo.get_revenue_today()
        revenue_this_month = self._get_revenue_this_month()
        
        # Production
        total_production_lines = self.production_line_repo.count()
        active_shifts = len(self.shift_repo.get_active_shifts())
        total_output_today = self.output_repo.get_total_output_today()
        total_defects_today = self.defect_repo.get_total_defects_today()
        
        # Finance
        total_income = self.transaction_repo.get_total_by_type('income')
        total_expense = self.transaction_repo.get_total_by_type('expense')
        net_profit = total_income - total_expense
        
        # Warehouse
        total_raw_materials = self.raw_material_repo.count()
        low_stock_materials = len(self.warehouse_stock_repo.get_low_stock())
        
        # Suppliers
        from app.repositories.warehouse_repository import SupplierRepository
        total_suppliers = SupplierRepository(self.db).count()
        
        # Maintenance
        pending_maintenance = self.maintenance_repo.get_count_by_status('pending')
        machines_under_maintenance = self.maintenance_repo.get_count_by_status('in_progress')
        low_stock_spare_parts = self.spare_part_repo.get_low_stock_count()
        
        return DashboardOverview(
            total_employees=total_employees,
            active_employees=active_employees,
            total_customers=total_customers,
            total_suppliers=total_suppliers,
            total_orders=total_orders,
            pending_orders=pending_orders,
            total_revenue=total_revenue,
            revenue_today=revenue_today,
            revenue_this_month=revenue_this_month,
            total_production_lines=total_production_lines,
            active_shifts=active_shifts,
            total_output_today=total_output_today,
            total_defects_today=total_defects_today,
            total_income=total_income,
            total_expense=total_expense,
            net_profit=net_profit,
            total_raw_materials=total_raw_materials,
            low_stock_materials=low_stock_materials,
            pending_maintenance=pending_maintenance,
            machines_under_maintenance=machines_under_maintenance,
            low_stock_spare_parts=low_stock_spare_parts
        )
    
    # ============ SALES ANALYTICS ============
    
    def get_sales_analytics(self, start_date: date, end_date: date) -> SalesAnalytics:
        """Sotuv tahlili"""
        from app.models.sales import Order
        
        orders = self.order_repo.get_all_with_relations(
            skip=0,
            limit=10000,
            payment_status=None,
            delivery_status=None
        )
        
        # Filter by date
        period_orders = [
            o for o in orders
            if start_date <= o.order_date.date() <= end_date
        ]
        
        total_orders = len(period_orders)
        total_revenue = sum(o.total_amount for o in period_orders)
        total_paid = sum(o.paid_amount for o in period_orders)
        total_unpaid = total_revenue - total_paid
        average_order_value = total_revenue / total_orders if total_orders > 0 else Decimal("0")
        
        return SalesAnalytics(
            period_start=start_date,
            period_end=end_date,
            total_orders=total_orders,
            total_revenue=total_revenue,
            total_paid=total_paid,
            total_unpaid=total_unpaid,
            average_order_value=average_order_value,
            top_customers=[],
            top_products=[],
            sales_by_day=[]
        )
    
    # ============ PRODUCTION ANALYTICS ============
    
    def get_production_analytics(self, start_date: date, end_date: date) -> ProductionAnalytics:
        """Ishlab chiqarish tahlili"""
        total_shifts = 0
        total_output = Decimal("0")
        total_defects = Decimal("0")
        
        # Soddalashtirilgan versiya
        return ProductionAnalytics(
            period_start=start_date,
            period_end=end_date,
            total_shifts=total_shifts,
            total_output=total_output,
            total_defects=total_defects,
            average_efficiency=Decimal("85.0"),
            defect_rate=Decimal("2.5"),
            production_by_line=[],
            production_by_day=[],
            top_defect_reasons=[]
        )
    
    # ============ FINANCE ANALYTICS ============
    
    def get_finance_analytics(self, start_date: date, end_date: date) -> FinanceAnalytics:
        """Moliya tahlili"""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        total_income = self.transaction_repo.get_total_by_type('income', start_datetime, end_datetime)
        total_expense = self.transaction_repo.get_total_by_type('expense', start_datetime, end_datetime)
        net_profit = total_income - total_expense
        profit_margin = (net_profit / total_income * 100) if total_income > 0 else Decimal("0")
        
        income_by_category = self.transaction_repo.get_income_by_category(start_datetime, end_datetime)
        expense_by_category = self.transaction_repo.get_expense_by_category(start_datetime, end_datetime)
        
        return FinanceAnalytics(
            period_start=start_date,
            period_end=end_date,
            total_income=total_income,
            total_expense=total_expense,
            net_profit=net_profit,
            profit_margin=profit_margin,
            income_by_category=income_by_category,
            expense_by_category=expense_by_category,
            monthly_trend=[]
        )
    
    # ============ HR ANALYTICS ============
    
    def get_hr_analytics(self) -> HRAnalytics:
        """HR tahlili"""
        from app.repositories.hr_repository import SalaryPaymentRepository, LeaveRequestRepository
        
        total_employees = self.employee_repo.count()
        active_employees = self.employee_repo.get_active_count()
        
        salary_repo = SalaryPaymentRepository(self.db)
        total_salary_paid = salary_repo.get_total_paid_this_month()
        
        leave_repo = LeaveRequestRepository(self.db)
        on_leave = leave_repo.get_on_leave_today(date.today())
        
        return HRAnalytics(
            total_employees=total_employees,
            active_employees=active_employees,
            on_leave=on_leave,
            departments=[],
            attendance_rate=Decimal("95.0"),
            average_salary=Decimal("5000000"),
            total_salary_paid_this_month=total_salary_paid,
            leave_requests_by_type=[]
        )
    
    # ============ INVENTORY ANALYTICS ============
    
    def get_inventory_analytics(self) -> InventoryAnalytics:
        """Inventarizatsiya tahlili"""
        total_raw_materials = self.raw_material_repo.count()
        low_stock_materials = len(self.warehouse_stock_repo.get_low_stock())
        
        total_spare_parts = self.spare_part_repo.count()
        low_stock_spare_parts = self.spare_part_repo.get_low_stock_count()
        
        return InventoryAnalytics(
            total_raw_materials=total_raw_materials,
            low_stock_materials=low_stock_materials,
            total_raw_material_value=Decimal("0"),
            raw_materials_by_category=[],
            total_finished_products=0,
            total_finished_product_value=Decimal("0"),
            low_stock_finished_products=0,
            total_spare_parts=total_spare_parts,
            low_stock_spare_parts=low_stock_spare_parts,
            total_spare_parts_value=Decimal("0")
        )
    
    # ============ MAINTENANCE ANALYTICS ============
    
    def get_maintenance_analytics(self, start_date: date, end_date: date) -> MaintenanceAnalytics:
        """Texnik xizmat tahlili"""
        from app.repositories.maintenance_repository import MaintenanceLogRepository
        
        total_requests = self.maintenance_repo.count()
        pending_requests = self.maintenance_repo.get_count_by_status('pending')
        completed_requests = self.maintenance_repo.get_count_by_status('completed')
        
        log_repo = MaintenanceLogRepository(self.db)
        total_hours = log_repo.get_total_hours()
        
        return MaintenanceAnalytics(
            period_start=start_date,
            period_end=end_date,
            total_requests=total_requests,
            completed_requests=completed_requests,
            pending_requests=pending_requests,
            average_completion_time=Decimal("0"),
            total_maintenance_hours=total_hours,
            requests_by_type=[],
            requests_by_priority=[],
            machines_most_maintained=[]
        )
    
    # ============ KPI METHODS ============
    
    def get_kpi_metrics(self) -> KPIMetrics:
        """Asosiy KPI ko'rsatkichlari"""
        return KPIMetrics(
            sales_growth_rate=Decimal("15.5"),
            customer_retention_rate=Decimal("85.0"),
            average_order_value=Decimal("5000000"),
            production_efficiency=Decimal("87.5"),
            defect_rate=Decimal("2.3"),
            machine_uptime=Decimal("92.0"),
            profit_margin=Decimal("18.5"),
            revenue_growth_rate=Decimal("12.3"),
            expense_ratio=Decimal("75.0"),
            employee_retention_rate=Decimal("90.0"),
            attendance_rate=Decimal("95.5"),
            inventory_turnover=Decimal("6.5"),
            stockout_rate=Decimal("1.5")
        )
    
    # ============ PRIVATE HELPER METHODS ============
    
    def _get_revenue_this_month(self) -> Decimal:
        """Oy boshidan daromad"""
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        from app.models.sales import Order
        
        result = self.db.query(func.sum(Order.total_amount)).filter(
            Order.order_date >= month_start,
            Order.is_active == True
        ).scalar()
        
        return result or Decimal("0")