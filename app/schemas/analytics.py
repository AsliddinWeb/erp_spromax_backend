from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal


# ============ DASHBOARD SCHEMAS ============

class DashboardOverview(BaseModel):
    """Asosiy dashboard ma'lumotlari"""
    # General
    total_employees: int
    active_employees: int
    total_customers: int
    total_suppliers: int
    
    # Sales
    total_orders: int
    pending_orders: int
    total_revenue: Decimal
    revenue_today: Decimal
    revenue_this_month: Decimal
    
    # Production
    total_production_lines: int
    active_shifts: int
    total_output_today: Decimal
    total_defects_today: Decimal
    
    # Finance
    total_income: Decimal
    total_expense: Decimal
    net_profit: Decimal
    
    # Warehouse
    total_raw_materials: int
    low_stock_materials: int
    
    # Maintenance
    pending_maintenance: int
    machines_under_maintenance: int
    low_stock_spare_parts: int


class SalesAnalytics(BaseModel):
    """Sotuv tahlili"""
    period_start: date
    period_end: date
    total_orders: int
    total_revenue: Decimal
    total_paid: Decimal
    total_unpaid: Decimal
    average_order_value: Decimal
    top_customers: List[Dict[str, Any]] = []
    top_products: List[Dict[str, Any]] = []
    sales_by_day: List[Dict[str, Any]] = []


class ProductionAnalytics(BaseModel):
    """Ishlab chiqarish tahlili"""
    period_start: date
    period_end: date
    total_shifts: int
    total_output: Decimal
    total_defects: Decimal
    average_efficiency: Decimal
    defect_rate: Decimal
    production_by_line: List[Dict[str, Any]] = []
    production_by_day: List[Dict[str, Any]] = []
    top_defect_reasons: List[Dict[str, Any]] = []


class FinanceAnalytics(BaseModel):
    """Moliya tahlili"""
    period_start: date
    period_end: date
    total_income: Decimal
    total_expense: Decimal
    net_profit: Decimal
    profit_margin: Decimal
    income_by_category: List[Dict[str, Any]] = []
    expense_by_category: List[Dict[str, Any]] = []
    monthly_trend: List[Dict[str, Any]] = []


class HRAnalytics(BaseModel):
    """HR tahlili"""
    total_employees: int
    active_employees: int
    on_leave: int
    departments: List[Dict[str, Any]] = []
    attendance_rate: Decimal
    average_salary: Decimal
    total_salary_paid_this_month: Decimal
    leave_requests_by_type: List[Dict[str, Any]] = []


class InventoryAnalytics(BaseModel):
    """Inventarizatsiya tahlili"""
    # Warehouse
    total_raw_materials: int
    low_stock_materials: int
    total_raw_material_value: Decimal
    raw_materials_by_category: List[Dict[str, Any]] = []
    
    # Finished Products
    total_finished_products: int
    total_finished_product_value: Decimal
    low_stock_finished_products: int
    
    # Spare Parts
    total_spare_parts: int
    low_stock_spare_parts: int
    total_spare_parts_value: Decimal


class MaintenanceAnalytics(BaseModel):
    """Texnik xizmat tahlili"""
    period_start: date
    period_end: date
    total_requests: int
    completed_requests: int
    pending_requests: int
    average_completion_time: Decimal  # hours
    total_maintenance_hours: Decimal
    requests_by_type: List[Dict[str, Any]] = []
    requests_by_priority: List[Dict[str, Any]] = []
    machines_most_maintained: List[Dict[str, Any]] = []


# ============ KPI SCHEMAS ============

class KPIMetrics(BaseModel):
    """Asosiy KPI ko'rsatkichlari"""
    # Sales KPIs
    sales_growth_rate: Decimal  # %
    customer_retention_rate: Decimal  # %
    average_order_value: Decimal
    
    # Production KPIs
    production_efficiency: Decimal  # %
    defect_rate: Decimal  # %
    machine_uptime: Decimal  # %
    
    # Finance KPIs
    profit_margin: Decimal  # %
    revenue_growth_rate: Decimal  # %
    expense_ratio: Decimal  # %
    
    # HR KPIs
    employee_retention_rate: Decimal  # %
    attendance_rate: Decimal  # %
    
    # Inventory KPIs
    inventory_turnover: Decimal
    stockout_rate: Decimal  # %


# ============ COMPARISON SCHEMAS ============

class PeriodComparison(BaseModel):
    """Davr taqqoslash"""
    metric_name: str
    current_period: Decimal
    previous_period: Decimal
    change_amount: Decimal
    change_percentage: Decimal
    trend: str  # "up", "down", "stable"


class ComparisonReport(BaseModel):
    """Taqqoslash hisoboti"""
    current_period_start: date
    current_period_end: date
    previous_period_start: date
    previous_period_end: date
    comparisons: List[PeriodComparison] = []