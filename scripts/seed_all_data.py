import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from datetime import date, datetime
from decimal import Decimal

# Import all models
from app.models.user import User, Role
from app.models.warehouse import Supplier, RawMaterial, WarehouseStock
from app.models.production import ProductionLine, FinishedProduct, FinishedProductStock
from app.models.sales import Customer
from app.models.finance import TransactionCategory
from app.models.hr import Department, Employee
from app.models.maintenance import SparePart

# Import services
from app.core.security import get_password_hash


def seed_all_data():
    """Barcha modullar uchun seed data"""
    db = SessionLocal()
    
    try:
        print("\n🌱 Seeding all data...\n")
        
        # 1. USERS & ROLES
        print("1️⃣ Creating users and roles...")
        
        # Admin role
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if not admin_role:
            admin_role = Role(name="Admin", description="System Administrator")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
        
        # Admin user
        admin = db.query(User).filter(User.email == "admin@spromax.uz").first()
        if not admin:
            admin = User(
                email="admin@spromax.uz",
                username="admin",
                full_name="System Administrator",
                hashed_password=get_password_hash("Admin123!"),
                role_id=admin_role.id,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print(f"   ✅ Admin user: admin@spromax.uz (username: admin) / Admin123!")
        else:
            print(f"   ℹ️  Admin user already exists")
        
        # 2. SUPPLIERS
        print("\n2️⃣ Creating suppliers...")
        suppliers_data = [
            {"name": "PVC Granules Supplier", "contact_person": "John Doe", "phone": "+998901111111"},
            {"name": "Chemical Additives Co", "contact_person": "Jane Smith", "phone": "+998902222222"},
            {"name": "Colorants International", "contact_person": "Bob Johnson", "phone": "+998903333333"}
        ]
        
        created_count = 0
        for s in suppliers_data:
            if not db.query(Supplier).filter(Supplier.phone == s["phone"]).first():
                db.add(Supplier(**s))
                created_count += 1
        db.commit()
        print(f"   ✅ {created_count} suppliers created")
        
        # 3. RAW MATERIALS (category field olib tashlandi)
        print("\n3️⃣ Creating raw materials...")
        
        first_supplier = db.query(Supplier).first()
        if not first_supplier:
            print("   ⚠️  No suppliers found, skipping raw materials")
        else:
            # RawMaterial modelida faqat: name, description, unit, minimum_stock, supplier_id bor
            materials_data = [
                {"name": "PVC Resin SG-5", "unit": "kg"},
                {"name": "Calcium Carbonate", "unit": "kg"},
                {"name": "Heat Stabilizer", "unit": "kg"}
            ]
            
            created_count = 0
            for m in materials_data:
                existing = db.query(RawMaterial).filter(RawMaterial.name == m["name"]).first()
                if not existing:
                    material = RawMaterial(**m)
                    db.add(material)
                    db.commit()
                    db.refresh(material)
                    
                    # Create warehouse stock
                    stock = WarehouseStock(
                        raw_material_id=material.id,
                        quantity=Decimal("0"),
                        last_updated=datetime.utcnow()
                    )
                    db.add(stock)
                    created_count += 1
            
            db.commit()
            print(f"   ✅ {created_count} raw materials created")
        
        # 4. PRODUCTION LINES
        print("\n4️⃣ Creating production lines...")
        lines_data = [
            {"name": "Line 1 - PVC Pipes", "capacity_per_hour": Decimal("500")},
            {"name": "Line 2 - PVC Fittings", "capacity_per_hour": Decimal("300")}
        ]
        
        created_count = 0
        for l in lines_data:
            if not db.query(ProductionLine).filter(ProductionLine.name == l["name"]).first():
                db.add(ProductionLine(**l))
                created_count += 1
        db.commit()
        print(f"   ✅ {created_count} production lines created")
        
        # 5. FINISHED PRODUCTS
        print("\n5️⃣ Creating finished products...")
        products_data = [
            {"name": "PVC Pipe Ø20mm", "unit": "meter", "standard_price": Decimal("5000")},
            {"name": "PVC Pipe Ø25mm", "unit": "meter", "standard_price": Decimal("7000")}
        ]
        
        created_count = 0
        for p in products_data:
            existing = db.query(FinishedProduct).filter(FinishedProduct.name == p["name"]).first()
            if not existing:
                product = FinishedProduct(**p)
                db.add(product)
                db.commit()
                db.refresh(product)
                
                # Create stock
                stock = FinishedProductStock(
                    finished_product_id=product.id,
                    quantity_total=Decimal("0"),
                    quantity_available=Decimal("0"),
                    quantity_reserved=Decimal("0"),
                    last_updated=datetime.utcnow()
                )
                db.add(stock)
                created_count += 1
        
        db.commit()
        print(f"   ✅ {created_count} finished products created")
        
        # 6. CUSTOMERS
        print("\n6️⃣ Creating customers...")
        customers_data = [
            {"name": "Construction Company A", "phone": "+998901234567", "customer_type": "wholesale"},
            {"name": "Retail Store B", "phone": "+998902345678", "customer_type": "regular"}
        ]
        
        created_count = 0
        for c in customers_data:
            if not db.query(Customer).filter(Customer.phone == c["phone"]).first():
                db.add(Customer(**c))
                created_count += 1
        db.commit()
        print(f"   ✅ {created_count} customers created")
        
        # 7. TRANSACTION CATEGORIES
        print("\n7️⃣ Creating transaction categories...")
        categories_data = [
            {"name": "Product Sales", "category_type": "income"},
            {"name": "Raw Material Purchase", "category_type": "expense"},
            {"name": "Salary Payment", "category_type": "expense"}
        ]
        
        created_count = 0
        for cat in categories_data:
            if not db.query(TransactionCategory).filter(TransactionCategory.name == cat["name"]).first():
                db.add(TransactionCategory(**cat))
                created_count += 1
        db.commit()
        print(f"   ✅ {created_count} transaction categories created")
        
        # 8. DEPARTMENTS
        print("\n8️⃣ Creating departments...")
        departments_data = [
            {"name": "Production Department"},
            {"name": "Sales Department"},
            {"name": "Administration"}
        ]
        
        created_depts = []
        created_count = 0
        for d in departments_data:
            existing = db.query(Department).filter(Department.name == d["name"]).first()
            if not existing:
                dept = Department(**d)
                db.add(dept)
                db.commit()
                db.refresh(dept)
                created_depts.append(dept)
                created_count += 1
            else:
                created_depts.append(existing)
        print(f"   ✅ {created_count} departments created")
        
        # 9. EMPLOYEES
        print("\n9️⃣ Creating employees...")
        if created_depts:
            employees_data = [
                {
                    "first_name": "Sardor", "last_name": "Karimov",
                    "phone": "+998901234560", "department_id": created_depts[0].id,
                    "position": "Production Manager", "hire_date": date(2020, 1, 15),
                    "salary": Decimal("8000000"), "employment_status": "active"
                }
            ]
            
            created_count = 0
            for e in employees_data:
                if not db.query(Employee).filter(Employee.phone == e["phone"]).first():
                    db.add(Employee(**e))
                    created_count += 1
            db.commit()
            print(f"   ✅ {created_count} employees created")
        
        # 10. SPARE PARTS
        print("\n🔟 Creating spare parts...")
        parts_data = [
            {"name": "Bearing 6205", "part_number": "BEARING-6205", "unit": "piece",
             "unit_price": Decimal("150000"), "quantity_in_stock": Decimal("20"),
             "min_stock_level": Decimal("10")}
        ]
        
        created_count = 0
        for p in parts_data:
            if not db.query(SparePart).filter(SparePart.part_number == p["part_number"]).first():
                db.add(SparePart(**p))
                created_count += 1
        db.commit()
        print(f"   ✅ {created_count} spare parts created")
        
        print("\n✅ ALL DATA SEEDED SUCCESSFULLY! 🎉\n")
        print("=" * 50)
        print("📝 LOGIN CREDENTIALS:")
        print("=" * 50)
        print("   Email:    admin@spromax.uz")
        print("   Username: admin")
        print("   Password: Admin123!")
        print("=" * 50)
        print("\n🌐 Access Points:")
        print("   Swagger UI: http://localhost:8000/docs")
        print("   Health:     http://localhost:8000/health\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all_data()