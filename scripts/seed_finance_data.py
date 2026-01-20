import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.finance import TransactionCategory


def seed_finance_data():
    """Finance test data"""
    db = SessionLocal()
    
    try:
        print("\n🌱 Finance seed data boshlandi...\n")
        
        # Transaction Categories - INCOME
        print("📝 Daromad kategoriyalari yaratilmoqda...")
        income_categories = [
            {
                "name": "Mahsulot sotish",
                "description": "Tayyor mahsulot sotishdan tushgan daromad",
                "category_type": "income"
            },
            {
                "name": "Xizmat ko'rsatish",
                "description": "Xizmat ko'rsatishdan daromad",
                "category_type": "income"
            },
            {
                "name": "Boshqa daromadlar",
                "description": "Qo'shimcha daromadlar",
                "category_type": "income"
            },
        ]
        
        for category_data in income_categories:
            existing = db.query(TransactionCategory).filter(
                TransactionCategory.name == category_data["name"]
            ).first()
            
            if not existing:
                category = TransactionCategory(**category_data)
                db.add(category)
        
        db.commit()
        print(f"✅ {len(income_categories)} ta daromad kategoriyasi yaratildi\n")
        
        # Transaction Categories - EXPENSE
        print("📝 Xarajat kategoriyalari yaratilmoqda...")
        expense_categories = [
            {
                "name": "Xom-ashyo xarid",
                "description": "Xom-ashyo sotib olish xarajatlari",
                "category_type": "expense"
            },
            {
                "name": "Ish haqi",
                "description": "Xodimlar ish haqi",
                "category_type": "expense"
            },
            {
                "name": "Kommunal xizmatlar",
                "description": "Elektr, suv, gaz to'lovlari",
                "category_type": "expense"
            },
            {
                "name": "Transport xarajatlari",
                "description": "Yuk tashish va transport xarajatlari",
                "category_type": "expense"
            },
            {
                "name": "Texnik xizmat ko'rsatish",
                "description": "Uskunalarni ta'mirlash va texnik xizmat",
                "category_type": "expense"
            },
            {
                "name": "Ofis xarajatlari",
                "description": "Ofis va boshqaruv xarajatlari",
                "category_type": "expense"
            },
            {
                "name": "Marketing va reklama",
                "description": "Marketing va reklama xarajatlari",
                "category_type": "expense"
            },
            {
                "name": "Boshqa xarajatlar",
                "description": "Qo'shimcha xarajatlar",
                "category_type": "expense"
            },
        ]
        
        for category_data in expense_categories:
            existing = db.query(TransactionCategory).filter(
                TransactionCategory.name == category_data["name"]
            ).first()
            
            if not existing:
                category = TransactionCategory(**category_data)
                db.add(category)
        
        db.commit()
        print(f"✅ {len(expense_categories)} ta xarajat kategoriyasi yaratildi\n")
        
        print("✅ Finance seed data tugadi!\n")
        print(f"📊 Jami: {len(income_categories) + len(expense_categories)} ta kategoriya yaratildi\n")
        
    except Exception as e:
        print(f"\n❌ Xatolik: {e}\n")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_finance_data()