from app.tasks.celery_app import celery_app
from app.tasks.warehouse_tasks import DatabaseTask
from app.utils.datetime_utils import get_now, get_today_start, get_month_start
from app.database import SessionLocal


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.report_tasks.daily_sales_summary')
def daily_sales_summary(self):
    """
    Kunlik sotuv xulosasini hisoblash.
    Har kuni soat 23:50 da ishga tushadi.
    """
    try:
        from app.services.sales_service import SalesService
        from app.models.sales import Order
        from sqlalchemy import func

        db = self.db
        today_start = get_today_start()
        now = get_now()

        orders = (
            db.query(Order)
            .filter(Order.order_date >= today_start, Order.order_date <= now)
            .all()
        )
        total_revenue = sum(float(o.total_amount) for o in orders)
        paid = sum(float(o.paid_amount) for o in orders)

        print(f"📊 Kunlik sotuv xulosasi ({now.strftime('%Y-%m-%d')}):")
        print(f"   Buyurtmalar soni: {len(orders)}")
        print(f"   Jami summa: {total_revenue:,.0f} so'm")
        print(f"   To'langan: {paid:,.0f} so'm")
        print(f"   Qarz: {total_revenue - paid:,.0f} so'm")

        return {
            "status": "success",
            "date": now.strftime("%Y-%m-%d"),
            "orders_count": len(orders),
            "total_revenue": total_revenue,
            "paid": paid,
            "debt": total_revenue - paid,
        }
    except Exception as e:
        print(f"❌ Kunlik sotuv xulosasida xatolik: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.report_tasks.daily_production_summary')
def daily_production_summary(self):
    """
    Kunlik ishlab chiqarish xulosasini hisoblash.
    Har kuni soat 23:55 da ishga tushadi.
    """
    try:
        from app.models.production import Shift, ProductionOutput

        db = self.db
        today_start = get_today_start()
        now = get_now()

        shifts = (
            db.query(Shift)
            .filter(Shift.start_time >= today_start)
            .all()
        )

        active = [s for s in shifts if s.status == "active"]
        completed = [s for s in shifts if s.status == "completed"]

        print(f"🏭 Kunlik ishlab chiqarish xulosasi ({now.strftime('%Y-%m-%d')}):")
        print(f"   Jami smenalar: {len(shifts)}")
        print(f"   Faol smenalar: {len(active)}")
        print(f"   Tugatilgan smenalar: {len(completed)}")

        return {
            "status": "success",
            "date": now.strftime("%Y-%m-%d"),
            "total_shifts": len(shifts),
            "active_shifts": len(active),
            "completed_shifts": len(completed),
        }
    except Exception as e:
        print(f"❌ Kunlik ishlab chiqarish xulosasida xatolik: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.report_tasks.clear_old_audit_logs')
def clear_old_audit_logs(self):
    """
    30 kundan eski audit loglarni o'chirish.
    Har haftada bir marta (dushanba 02:00) ishga tushadi.
    """
    try:
        from app.models.audit_log import AuditLog
        from datetime import timedelta

        db = self.db
        cutoff = get_now() - timedelta(days=30)
        deleted = db.query(AuditLog).filter(AuditLog.created_at < cutoff).delete()
        db.commit()

        print(f"🧹 {deleted} ta eski audit log o'chirildi (30 kundan eski)")
        return {"status": "success", "deleted_count": deleted}
    except Exception as e:
        print(f"❌ Audit log tozalashda xatolik: {e}")
        return {"status": "error", "message": str(e)}
