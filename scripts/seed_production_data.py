import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

sys.path.append(str(Path(__file__).parent.parent))

import app.models.maintenance  # noqa

from app.database import SessionLocal
from app.models.production import (
    ProductionLine,
    Machine,
    FinishedProduct,
    DefectReason,
    FinishedProductStock
)


def seed_production_data():
    """Production test data"""
    db = SessionLocal()
    
    try:
        print("\n🌱 Production seed data boshlandi...\n")
        
        # Production Lines
        print("📝 Production lines yaratilmoqda...")
        lines_data = [
            {
                "name": "Liniya 1 - PVX Quvurlar",
                "description": "PVX quvurlar ishlab chiqarish liniyasi",
                "capacity_per_hour": Decimal("500")
            },
            {
                "name": "Liniya 2 - PVX Fitinglar",
                "description": "PVX fitinglar ishlab chiqarish liniyasi",
                "capacity_per_hour": Decimal("300")
            },
            {
                "name": "Liniya 3 - PVX Panellar",
                "description": "PVX devorativ panellar ishlab chiqarish liniyasi",
                "capacity_per_hour": Decimal("400")
            }
        ]
        
        created_lines = []
        for line_data in lines_data:
            existing = db.query(ProductionLine).filter(
                ProductionLine.name == line_data["name"]
            ).first()
            
            if not existing:
                line = ProductionLine(**line_data)
                db.add(line)
                db.commit()
                db.refresh(line)
                created_lines.append(line)
            else:
                created_lines.append(existing)
        
        print(f"✅ {len(lines_data)} ta production line yaratildi\n")
        
        # Machines
        print("📝 Mashinalar yaratilmoqda...")
        machines_data = [
            # Liniya 1 mashinalari
            {"name": "Ekstruder 1-A", "serial_number": "EXT-001", "line": created_lines[0]},
            {"name": "Ekstruder 1-B", "serial_number": "EXT-002", "line": created_lines[0]},
            {"name": "Kesish mashinasi 1", "serial_number": "CUT-001", "line": created_lines[0]},
            # Liniya 2 mashinalari
            {"name": "Ekstruder 2-A", "serial_number": "EXT-003", "line": created_lines[1]},
            {"name": "Qoliplash mashinasi 2", "serial_number": "MLD-001", "line": created_lines[1]},
            # Liniya 3 mashinalari
            {"name": "Ekstruder 3-A", "serial_number": "EXT-004", "line": created_lines[2]},
            {"name": "Laminat press 3", "serial_number": "LAM-001", "line": created_lines[2]},
        ]
        
        for machine_data in machines_data:
            existing = db.query(Machine).filter(
                Machine.serial_number == machine_data["serial_number"]
            ).first()
            
            if not existing:
                machine = Machine(
                    name=machine_data["name"],
                    serial_number=machine_data["serial_number"],
                    production_line_id=machine_data["line"].id,
                    status="active"
                )
                db.add(machine)
        
        db.commit()
        print(f"✅ {len(machines_data)} ta mashina yaratildi\n")
        
        # Finished Products
        print("📝 Tayyor mahsulotlar yaratilmoqda...")
        products_data = [
            {
                "name": "PVX quvur Ø20mm",
                "description": "20mm diametrli PVX quvur",
                "unit": "metr",
                "standard_price": Decimal("5000")
            },
            {
                "name": "PVX quvur Ø25mm",
                "description": "25mm diametrli PVX quvur",
                "unit": "metr",
                "standard_price": Decimal("7000")
            },
            {
                "name": "PVX quvur Ø32mm",
                "description": "32mm diametrli PVX quvur",
                "unit": "metr",
                "standard_price": Decimal("9000")
            },
            {
                "name": "PVX fitting - Burchak 90°",
                "description": "90 gradusli PVX burchak fitting",
                "unit": "dona",
                "standard_price": Decimal("3000")
            },
            {
                "name": "PVX fitting - T-shakl",
                "description": "T-shaklli PVX fitting",
                "unit": "dona",
                "standard_price": Decimal("4000")
            },
            {
                "name": "PVX devor paneli - Oq",
                "description": "Oq rangdagi PVX devor paneli",
                "unit": "metr",
                "standard_price": Decimal("25000")
            },
        ]
        
        for product_data in products_data:
            existing = db.query(FinishedProduct).filter(
                FinishedProduct.name == product_data["name"]
            ).first()
            
            if not existing:
                product = FinishedProduct(**product_data)
                db.add(product)
                db.commit()
                db.refresh(product)
                
                # Stock yaratish
                stock = FinishedProductStock(
                    finished_product_id=product.id,
                    quantity_total=Decimal("0"),
                    quantity_available=Decimal("0"),
                    quantity_reserved=Decimal("0"),
                    last_updated=datetime.utcnow()
                )
                db.add(stock)
        
        db.commit()
        print(f"✅ {len(products_data)} ta tayyor mahsulot yaratildi\n")
        
        # Defect Reasons
        print("📝 Brak sabablari yaratilmoqda...")
        defect_reasons_data = [
            {"name": "Material iflos", "description": "Xom-ashyoda ifloslantirish"},
            {"name": "Harorat noto'g'ri", "description": "Ishlov berish harorati noto'g'ri"},
            {"name": "Mashina nosozligi", "description": "Uskuna texnik nosozligi"},
            {"name": "Operator xatosi", "description": "Operator tomonidan xatolik"},
            {"name": "O'lchov noto'g'ri", "description": "O'lchamlar standartga to'g'ri kelmaydi"},
        ]
        
        for reason_data in defect_reasons_data:
            existing = db.query(DefectReason).filter(
                DefectReason.name == reason_data["name"]
            ).first()
            
            if not existing:
                reason = DefectReason(**reason_data)
                db.add(reason)
        
        db.commit()
        print(f"✅ {len(defect_reasons_data)} ta brak sababi yaratildi\n")
        
        print("✅ Production seed data tugadi!\n")
        
    except Exception as e:
        print(f"\n❌ Xatolik: {e}\n")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_production_data()