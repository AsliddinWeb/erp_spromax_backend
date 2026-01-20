import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.warehouse import Supplier, RawMaterial, WarehouseStock


def seed_warehouse_data():
    """Warehouse test data"""
    db = SessionLocal()
    
    try:
        print("\n🌱 Warehouse seed data boshlandi...\n")
        
        # Suppliers
        print("📝 Suppliers yaratilmoqda...")
        suppliers_data = [
            {
                "name": "PVX Plast Tashkent",
                "contact_person": "Akmal Karimov",
                "phone": "+998901234567",
                "email": "info@pvxplast.uz",
                "address": "Toshkent sh., Chilonzor t.",
                "inn": "123456789"
            },
            {
                "name": "Chimplast LLC",
                "contact_person": "Sardor Alimov",
                "phone": "+998901234568",
                "email": "sales@chimplast.uz",
                "address": "Toshkent sh., Yakkasaroy t.",
                "inn": "987654321"
            },
            {
                "name": "Import Materials Co",
                "contact_person": "John Smith",
                "phone": "+998901234569",
                "email": "contact@importmat.com",
                "address": "Toshkent sh., Yunusobod t."
            }
        ]
        
        for supplier_data in suppliers_data:
            existing = db.query(Supplier).filter(
                Supplier.name == supplier_data["name"]
            ).first()
            
            if not existing:
                supplier = Supplier(**supplier_data)
                db.add(supplier)
        
        db.commit()
        print(f"✅ {len(suppliers_data)} ta supplier yaratildi\n")
        
        # Raw Materials
        print("📝 Xom-ashyolar yaratilmoqda...")
        materials_data = [
            {
                "name": "PVX granula (white)",
                "description": "Oq rangdagi PVX granulasi",
                "unit": "kg",
                "minimum_stock": Decimal("500")
            },
            {
                "name": "PVX granula (grey)",
                "description": "Kulrang PVX granulasi",
                "unit": "kg",
                "minimum_stock": Decimal("300")
            },
            {
                "name": "Stabilizator",
                "description": "PVX uchun stabilizator",
                "unit": "kg",
                "minimum_stock": Decimal("100")
            },
            {
                "name": "Plastifikator",
                "description": "Plastifikator qo'shimchasi",
                "unit": "litr",
                "minimum_stock": Decimal("50")
            },
            {
                "name": "Bo'yoq pigment (qora)",
                "description": "Qora rang pigmenti",
                "unit": "kg",
                "minimum_stock": Decimal("20")
            }
        ]
        
        for material_data in materials_data:
            existing = db.query(RawMaterial).filter(
                RawMaterial.name == material_data["name"]
            ).first()
            
            if not existing:
                material = RawMaterial(**material_data)
                db.add(material)
                db.commit()
                db.refresh(material)
                
                # Stock yaratish
                stock = WarehouseStock(
                    raw_material_id=material.id,
                    quantity=Decimal("0"),
                    last_updated=datetime.utcnow()
                )
                db.add(stock)
        
        db.commit()
        print(f"✅ {len(materials_data)} ta xom-ashyo yaratildi\n")
        
        print("✅ Warehouse seed data tugadi!\n")
        
    except Exception as e:
        print(f"\n❌ Xatolik: {e}\n")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_warehouse_data()