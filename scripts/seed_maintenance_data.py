import sys
from pathlib import Path
from decimal import Decimal

sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.maintenance import SparePart


def seed_maintenance_data():
    """Maintenance test data"""
    db = SessionLocal()
    
    try:
        print("\n🌱 Maintenance seed data boshlandi...\n")
        
        # Spare Parts
        print("📝 Ehtiyot qismlar yaratilmoqda...")
        spare_parts_data = [
            {
                "name": "Ekstruder vint",
                "part_number": "EXT-SCREW-001",
                "description": "Ekstruder uchun asosiy vint",
                "unit": "dona",
                "unit_price": Decimal("2500000"),
                "quantity_in_stock": Decimal("5"),
                "min_stock_level": Decimal("2")
            },
            {
                "name": "Elektr motor",
                "part_number": "MOTOR-3KW-001",
                "description": "3 kW elektr motor",
                "unit": "dona",
                "unit_price": Decimal("3000000"),
                "quantity_in_stock": Decimal("3"),
                "min_stock_level": Decimal("1")
            },
            {
                "name": "Podshipnik 6205",
                "part_number": "BEARING-6205",
                "description": "Stanok podshipnigi 6205",
                "unit": "dona",
                "unit_price": Decimal("150000"),
                "quantity_in_stock": Decimal("20"),
                "min_stock_level": Decimal("10")
            },
            {
                "name": "Pichoq to'plami",
                "part_number": "BLADE-SET-001",
                "description": "Kesish mashinasi uchun picholar",
                "unit": "to'plam",
                "unit_price": Decimal("800000"),
                "quantity_in_stock": Decimal("4"),
                "min_stock_level": Decimal("2")
            },
            {
                "name": "Termostat sensori",
                "part_number": "THERMO-SENSOR-01",
                "description": "Harorat o'lchash sensori",
                "unit": "dona",
                "unit_price": Decimal("450000"),
                "quantity_in_stock": Decimal("8"),
                "min_stock_level": Decimal("5")
            },
            {
                "name": "Rezina prokat",
                "part_number": "RUBBER-ROLL-001",
                "description": "Laminat press uchun rezina prokat",
                "unit": "metr",
                "unit_price": Decimal("120000"),
                "quantity_in_stock": Decimal("15"),
                "min_stock_level": Decimal("10")
            },
        ]
        
        for part_data in spare_parts_data:
            existing = db.query(SparePart).filter(
                SparePart.part_number == part_data["part_number"]
            ).first()
            
            if not existing:
                part = SparePart(**part_data)
                db.add(part)
        
        db.commit()
        print(f"✅ {len(spare_parts_data)} ta ehtiyot qism yaratildi\n")
        
        print("✅ Maintenance seed data tugadi!\n")
        
    except Exception as e:
        print(f"\n❌ Xatolik: {e}\n")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_maintenance_data()