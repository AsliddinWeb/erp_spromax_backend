from celery import Task
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.services.warehouse_service import WarehouseService


class DatabaseTask(Task):
    """Base task with database session"""
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.warehouse_tasks.check_low_stock')
def check_low_stock(self):
    """
    Kam qoldiqlarni tekshirish va notification yuborish
    
    Har soat ishga tushadi va minimum_stock dan kam bo'lgan
    xom-ashyolar ro'yxatini oladi.
    """
    try:
        service = WarehouseService(self.db)
        low_stock_items = service.get_low_stock_items()
        
        if low_stock_items:
            # TODO: Email yoki SMS notification yuborish
            print(f"⚠️  Kam qoldiqlar aniqlandi: {len(low_stock_items)} ta xom-ashyo")
            
            for item in low_stock_items:
                print(f"  - {item.raw_material_name}: {item.current_stock} {item.unit} "
                      f"(minimum: {item.minimum_stock} {item.unit})")
            
            return {
                "status": "success",
                "low_stock_count": len(low_stock_items),
                "items": [item.raw_material_name for item in low_stock_items]
            }
        else:
            print("✅ Barcha xom-ashyolar yetarli miqdorda")
            return {
                "status": "success",
                "low_stock_count": 0,
                "items": []
            }
            
    except Exception as e:
        print(f"❌ Xatolik: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@celery_app.task(base=DatabaseTask, bind=True, name='app.tasks.warehouse_tasks.generate_stock_report')
def generate_stock_report(self):
    """
    Ombor hisobotini generatsiya qilish
    
    Haftalik yoki oylik ishlatilishi mumkin.
    """
    try:
        service = WarehouseService(self.db)
        
        # Statistika olish
        stats = service.get_statistics()
        
        # Barcha qoldiqlar
        stock = service.get_all_stock(skip=0, limit=1000)
        
        print(f"📊 Ombor hisoboti:")
        print(f"  - Jami xom-ashyolar: {stats.total_raw_materials}")
        print(f"  - Jami yetkazib beruvchilar: {stats.total_suppliers}")
        print(f"  - Kam qoldiqlar: {stats.low_stock_items_count}")
        print(f"  - Kutilayotgan so'rovlar: {stats.pending_requests_count}")
        print(f"  - Ushbu oy qabul qilishlar: {stats.total_receipts_this_month}")
        
        # TODO: PDF yoki Excel hisobot yaratish
        
        return {
            "status": "success",
            "statistics": {
                "total_raw_materials": stats.total_raw_materials,
                "total_suppliers": stats.total_suppliers,
                "low_stock_items": stats.low_stock_items_count,
                "pending_requests": stats.pending_requests_count
            }
        }
        
    except Exception as e:
        print(f"❌ Xatolik: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }