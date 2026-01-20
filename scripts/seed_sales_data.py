import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.sales import Customer


def seed_sales_data():
    """Sales test data"""
    db = SessionLocal()
    
    try:
        print("\n🌱 Sales seed data boshlandi...\n")
        
        # Customers
        print("📝 Mijozlar yaratilmoqda...")
        customers_data = [
            {
                "name": "Qurilish Kompaniyasi \"Zamin\"",
                "contact_person": "Rustam Valiyev",
                "phone": "+998901111111",
                "email": "info@zamin.uz",
                "address": "Toshkent sh., Mirzo Ulug'bek t., 100-uy",
                "inn": "201234567",
                "customer_type": "wholesale"
            },
            {
                "name": "Avto Servis \"Texno\"",
                "contact_person": "Jamshid Ergashev",
                "phone": "+998902222222",
                "email": "texno@mail.uz",
                "address": "Toshkent sh., Chilonzor t., 50-uy",
                "inn": "202345678",
                "customer_type": "regular"
            },
            {
                "name": "Do'kon \"Qurilish Materiallari\"",
                "contact_person": "Nodira Karimova",
                "phone": "+998903333333",
                "email": "qurilish@gmail.com",
                "address": "Samarqand sh., Amir Temur ko'chasi",
                "inn": "203456789",
                "customer_type": "wholesale"
            },
            {
                "name": "Individual - Aziz Tursunov",
                "contact_person": "Aziz Tursunov",
                "phone": "+998904444444",
                "email": "aziz.t@mail.ru",
                "address": "Toshkent sh., Yunusobod t.",
                "customer_type": "regular"
            },
            {
                "name": "TD \"Megastroy\"",
                "contact_person": "Davron Rahimov",
                "phone": "+998905555555",
                "email": "megastroy@company.uz",
                "address": "Toshkent sh., Sergeli t., Ipak Yo'li",
                "inn": "204567890",
                "customer_type": "vip"
            },
            {
                "name": "Uy Ta'mirlash Markazi",
                "contact_person": "Shoxrux Normatov",
                "phone": "+998906666666",
                "email": "tamirlash@gmail.com",
                "address": "Andijon sh., Markaziy ko'cha",
                "customer_type": "regular"
            },
        ]
        
        for customer_data in customers_data:
            existing = db.query(Customer).filter(
                Customer.phone == customer_data["phone"]
            ).first()
            
            if not existing:
                customer = Customer(**customer_data)
                db.add(customer)
        
        db.commit()
        print(f"✅ {len(customers_data)} ta mijoz yaratildi\n")
        
        print("✅ Sales seed data tugadi!\n")
        
    except Exception as e:
        print(f"\n❌ Xatolik: {e}\n")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_sales_data()