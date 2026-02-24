import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal, Base, engine
from app.models.user import User, Role, Permission
from app.models.warehouse import Supplier, RawMaterial, WarehouseReceipt, WarehouseStock, MaterialRequest
from app.models.production import (
    ProductionLine, Machine, FinishedProduct, Shift, ShiftMachine,
    ProductionRecord, ProductionOutput, DefectReason, DefectiveProduct,
    ShiftHandover, FinishedProductStock
)
from app.models.sales import Customer, Order, OrderItem, Payment
from app.models.finance import TransactionCategory, FinancialTransaction
from app.models.hr import Department, Employee, Attendance, SalaryPayment, LeaveRequest
from app.models.maintenance import (
    MaintenanceRequest, MaintenanceLog, SparePart,
    SparePartUsage, MaintenanceSchedule
)


def clear_database():
    """Database'dagi barcha ma'lumotlarni o'chirish"""
    db = SessionLocal()
    
    try:
        print("\n🗑️  Database tozalanmoqda...\n")
        
        # Foreign key constraint'lar tufayli tartib muhim!
        
        # 1. Maintenance module
        print("🔧 Maintenance data o'chirilmoqda...")
        db.query(SparePartUsage).delete()
        db.query(MaintenanceLog).delete()
        db.query(MaintenanceSchedule).delete()
        db.query(MaintenanceRequest).delete()
        db.query(SparePart).delete()
        db.commit()
        
        # 2. HR module
        print("👥 HR data o'chirilmoqda...")
        db.query(LeaveRequest).delete()
        db.query(SalaryPayment).delete()
        db.query(Attendance).delete()
        db.query(Employee).delete()
        db.query(Department).delete()
        db.commit()
        
        # 3. Finance module
        print("💰 Finance data o'chirilmoqda...")
        db.query(FinancialTransaction).delete()
        db.query(TransactionCategory).delete()
        db.commit()
        
        # 4. Sales module
        print("🛒 Sales data o'chirilmoqda...")
        db.query(Payment).delete()
        db.query(OrderItem).delete()
        db.query(Order).delete()
        db.query(Customer).delete()
        db.commit()
        
        # 5. Production module
        print("🏭 Production data o'chirilmoqda...")
        db.query(ShiftHandover).delete()
        db.query(DefectiveProduct).delete()
        db.query(ProductionOutput).delete()
        db.query(ProductionRecord).delete()
        db.query(ShiftMachine).delete()
        db.query(Shift).delete()
        db.query(DefectReason).delete()
        db.query(FinishedProductStock).delete()
        db.query(FinishedProduct).delete()
        db.query(Machine).delete()
        db.query(ProductionLine).delete()
        db.commit()
        
        # 6. Warehouse module
        print("📦 Warehouse data o'chirilmoqda...")
        db.query(MaterialRequest).delete()
        db.query(WarehouseStock).delete()
        db.query(WarehouseReceipt).delete()
        db.query(RawMaterial).delete()
        db.query(Supplier).delete()
        db.commit()
        
        # 7. Users, Roles, Permissions (oxirida)
        print("👤 Users, Roles, Permissions o'chirilmoqda...")
        db.query(User).delete()
        
        # Role-Permission many-to-many munosabatini o'chirish
        from app.models.user import role_permissions
        db.execute(role_permissions.delete())
        
        db.query(Role).delete()
        db.query(Permission).delete()
        db.commit()
        
        print("\n✅ Database muvaffaqiyatli tozalandi!\n")
        
    except Exception as e:
        print(f"\n❌ Xatolik: {e}\n")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    # Tasdiqlash
    print("⚠️  DIQQAT: Bu barcha ma'lumotlarni o'chiradi!")
    response = input("Davom etishni xohlaysizmi? (yes/no): ").strip().lower()
    
    if response == "yes":
        clear_database()
    else:
        print("❌ Bekor qilindi")
        sys.exit(0)