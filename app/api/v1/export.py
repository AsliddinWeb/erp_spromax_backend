from datetime import date
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, require_permission
from app.models.user import User
from app.models.sales import Order, Customer, OrderItem
from app.models.warehouse import WarehouseStock, RawMaterial
from app.models.production import Shift, ProductionOutput, FinishedProduct
from app.core.constants import PermissionType
from app.utils.excel_export import build_workbook
from app.utils.datetime_utils import get_now

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/orders")
def export_orders(
    start_date: date = Query(default=None, description="Boshlang'ich sana"),
    end_date: date = Query(default=None, description="Tugash sanasi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_SALES)),
):
    """Buyurtmalarni Excel formatida yuklab olish"""
    query = (
        db.query(Order, Customer)
        .join(Customer, Order.customer_id == Customer.id)
        .filter(Order.is_active == True)
    )
    if start_date:
        query = query.filter(Order.order_date >= start_date)
    if end_date:
        query = query.filter(Order.order_date <= end_date)

    rows = []
    for order, customer in query.order_by(Order.order_date.desc()).all():
        rows.append([
            str(order.id)[:8],
            customer.name,
            customer.phone,
            str(order.order_date)[:16] if order.order_date else "",
            float(order.total_amount),
            float(order.paid_amount),
            order.payment_status,
            order.delivery_status,
            str(order.created_at)[:16] if order.created_at else "",
        ])

    data = build_workbook([{
        "title": "Buyurtmalar",
        "headers": [
            "ID", "Mijoz", "Telefon", "Buyurtma sanasi",
            "Jami summa", "To'langan", "To'lov holati",
            "Yetkazib berish holati", "Yaratilgan",
        ],
        "rows": rows,
    }])

    filename = f"orders_{get_now().strftime('%Y%m%d_%H%M')}.xlsx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/warehouse-stock")
def export_warehouse_stock(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_WAREHOUSE)),
):
    """Ombor qoldiqlarini Excel formatida yuklab olish"""
    results = (
        db.query(WarehouseStock, RawMaterial)
        .join(RawMaterial, WarehouseStock.raw_material_id == RawMaterial.id)
        .filter(RawMaterial.is_active == True)
        .order_by(RawMaterial.name)
        .all()
    )

    rows = []
    for stock, material in results:
        status = "Yetarli"
        if material.minimum_stock and stock.current_stock < material.minimum_stock:
            status = "KAM QOLGAN"
        rows.append([
            material.name,
            material.unit,
            float(stock.current_stock),
            float(material.minimum_stock) if material.minimum_stock else "",
            status,
            str(stock.updated_at)[:16] if stock.updated_at else "",
        ])

    data = build_workbook([{
        "title": "Ombor qoldiqlari",
        "headers": ["Xom-ashyo", "O'lchov", "Joriy qoldiq", "Minimum", "Holat", "Yangilangan"],
        "rows": rows,
    }])

    filename = f"warehouse_stock_{get_now().strftime('%Y%m%d_%H%M')}.xlsx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/production-shifts")
def export_production_shifts(
    start_date: date = Query(default=None, description="Boshlang'ich sana"),
    end_date: date = Query(default=None, description="Tugash sanasi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_PRODUCTION)),
):
    """Smenalar hisobotini Excel formatida yuklab olish"""
    query = db.query(Shift).filter(Shift.is_active == True)
    if start_date:
        query = query.filter(Shift.start_time >= start_date)
    if end_date:
        query = query.filter(Shift.start_time <= end_date)

    rows = []
    for shift in query.order_by(Shift.start_time.desc()).all():
        rows.append([
            str(shift.shift_number) if hasattr(shift, "shift_number") else str(shift.id)[:8],
            str(shift.start_time)[:16] if shift.start_time else "",
            str(shift.end_time)[:16] if shift.end_time else "",
            shift.status,
            float(shift.total_output) if hasattr(shift, "total_output") and shift.total_output else 0,
            float(shift.total_defects) if hasattr(shift, "total_defects") and shift.total_defects else 0,
            str(shift.created_at)[:16] if shift.created_at else "",
        ])

    data = build_workbook([{
        "title": "Smenalar",
        "headers": ["Smena №", "Boshlash", "Tugash", "Holat", "Ishlab chiqarildi", "Brak", "Yaratilgan"],
        "rows": rows,
    }])

    filename = f"shifts_{get_now().strftime('%Y%m%d_%H%M')}.xlsx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
