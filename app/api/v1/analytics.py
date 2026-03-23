from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from app.database import get_db
from app.schemas.analytics import (
    DashboardOverview,
    SalesAnalytics,
    ProductionAnalytics,
    FinanceAnalytics,
    HRAnalytics,
    InventoryAnalytics,
    MaintenanceAnalytics,
    KPIMetrics
)
from app.services.analytics_service import AnalyticsService
from app.dependencies import get_current_user, require_permission
from app.models.user import User
from app.core.constants import PermissionType
from app.core.cache import cache_get, cache_set

router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])


# ============ DASHBOARD ENDPOINT ============

@router.get("/dashboard", response_model=DashboardOverview)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Asosiy dashboard ma'lumotlari (5 daqiqa cache)

    Barcha modullardan umumiy ko'rsatkichlar.
    """
    cache_key = f"analytics:dashboard:{date.today()}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    service = AnalyticsService(db)
    result = service.get_dashboard_overview()
    cache_set(cache_key, jsonable_encoder(result), ttl=300)
    return result


# ============ MODULE ANALYTICS ENDPOINTS ============

@router.get("/sales", response_model=SalesAnalytics)
async def get_sales_analytics(
    start_date: date = Query(..., description="Boshlang'ich sana"),
    end_date: date = Query(..., description="Tugash sanasi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    """
    Sotuv tahlili
    
    Belgilangan davr uchun sotuvlar statistikasi va tahlili.
    """
    service = AnalyticsService(db)
    return service.get_sales_analytics(start_date, end_date)


@router.get("/production", response_model=ProductionAnalytics)
async def get_production_analytics(
    start_date: date = Query(..., description="Boshlang'ich sana"),
    end_date: date = Query(..., description="Tugash sanasi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION))
):
    """
    Ishlab chiqarish tahlili
    
    Ishlab chiqarish samaradorligi, brak darajasi va boshqa ko'rsatkichlar.
    """
    service = AnalyticsService(db)
    return service.get_production_analytics(start_date, end_date)


@router.get("/finance", response_model=FinanceAnalytics)
async def get_finance_analytics(
    start_date: date = Query(..., description="Boshlang'ich sana"),
    end_date: date = Query(..., description="Tugash sanasi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_FINANCE))
):
    """
    Moliyaviy tahlil
    
    Daromad, xarajat, foyda va moliyaviy ko'rsatkichlar.
    """
    service = AnalyticsService(db)
    return service.get_finance_analytics(start_date, end_date)


@router.get("/hr", response_model=HRAnalytics)
async def get_hr_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_HR))
):
    """
    HR tahlili
    
    Xodimlar, davomat, ish haqi va boshqa HR ko'rsatkichlari.
    """
    service = AnalyticsService(db)
    return service.get_hr_analytics()


@router.get("/inventory", response_model=InventoryAnalytics)
async def get_inventory_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE))
):
    """
    Inventarizatsiya tahlili
    
    Xom-ashyo, tayyor mahsulotlar va ehtiyot qismlar inventarizatsiyasi.
    """
    service = AnalyticsService(db)
    return service.get_inventory_analytics()


@router.get("/maintenance", response_model=MaintenanceAnalytics)
async def get_maintenance_analytics(
    start_date: date = Query(..., description="Boshlang'ich sana"),
    end_date: date = Query(..., description="Tugash sanasi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Texnik xizmat tahlili
    
    Texnik xizmat so'rovlari, bajarilgan ishlar va uskunalar holati.
    """
    service = AnalyticsService(db)
    return service.get_maintenance_analytics(start_date, end_date)


# ============ KPI ENDPOINT ============

@router.get("/kpi", response_model=KPIMetrics)
async def get_kpi_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Asosiy KPI ko'rsatkichlari (10 daqiqa cache)

    Kompaniyaning barcha asosiy ko'rsatkichlari (KPI - Key Performance Indicators).
    """
    cache_key = f"analytics:kpi:{date.today()}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    service = AnalyticsService(db)
    result = service.get_kpi_metrics()
    cache_set(cache_key, jsonable_encoder(result), ttl=600)
    return result


# ============ QUICK STATS ENDPOINTS ============

@router.get("/quick-stats/today")
async def get_today_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bugungi tezkor statistika
    
    Bugun uchun eng muhim ko'rsatkichlar.
    """
    service = AnalyticsService(db)
    dashboard = service.get_dashboard_overview()
    
    return {
        "date": date.today(),
        "revenue_today": dashboard.revenue_today,
        "output_today": dashboard.total_output_today,
        "defects_today": dashboard.total_defects_today,
        "active_shifts": dashboard.active_shifts,
        "pending_orders": dashboard.pending_orders,
        "pending_maintenance": dashboard.pending_maintenance
    }


@router.get("/quick-stats/this-month")
async def get_this_month_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Shu oy statistikasi
    
    Joriy oy uchun umumiy ko'rsatkichlar.
    """
    service = AnalyticsService(db)
    dashboard = service.get_dashboard_overview()
    
    # Oy statistikasi
    month_start = date.today().replace(day=1)
    month_end = date.today()
    
    finance_analytics = service.get_finance_analytics(month_start, month_end)
    
    return {
        "month": date.today().strftime("%B %Y"),
        "revenue": dashboard.revenue_this_month,
        "total_income": finance_analytics.total_income,
        "total_expense": finance_analytics.total_expense,
        "net_profit": finance_analytics.net_profit,
        "profit_margin": finance_analytics.profit_margin,
        "total_orders": dashboard.total_orders
    }


@router.get("/quick-stats/alerts")
async def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tizim ogohlantirishlari
    
    Diqqat talab qiladigan holatlar.
    """
    service = AnalyticsService(db)
    dashboard = service.get_dashboard_overview()
    
    alerts = []
    
    # Low stock alerts
    if dashboard.low_stock_materials > 0:
        alerts.append({
            "type": "warning",
            "category": "warehouse",
            "message": f"{dashboard.low_stock_materials} ta xom-ashyo kam qolgan",
            "severity": "medium"
        })
    
    if dashboard.low_stock_spare_parts > 0:
        alerts.append({
            "type": "warning",
            "category": "maintenance",
            "message": f"{dashboard.low_stock_spare_parts} ta ehtiyot qism kam qolgan",
            "severity": "medium"
        })
    
    # Maintenance alerts
    if dashboard.pending_maintenance > 5:
        alerts.append({
            "type": "warning",
            "category": "maintenance",
            "message": f"{dashboard.pending_maintenance} ta texnik xizmat so'rovi kutmoqda",
            "severity": "high"
        })
    
    # Order alerts
    if dashboard.pending_orders > 10:
        alerts.append({
            "type": "info",
            "category": "sales",
            "message": f"{dashboard.pending_orders} ta buyurtma kutilmoqda",
            "severity": "low"
        })
    
    return {
        "total_alerts": len(alerts),
        "alerts": alerts
    }