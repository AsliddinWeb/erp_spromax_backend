import sys
from pathlib import Path
from datetime import date
from decimal import Decimal

sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.hr import Department, Employee


def seed_hr_data():
    """HR test data"""
    db = SessionLocal()
    
    try:
        print("\n🌱 HR seed data boshlandi...\n")
        
        # Departments
        print("📝 Bo'limlar yaratilmoqda...")
        departments_data = [
            {"name": "Ishlab chiqarish bo'limi", "description": "Asosiy ishlab chiqarish jarayoni"},
            {"name": "Savdo bo'limi", "description": "Sotish va mijozlar bilan ishlash"},
            {"name": "Moliya bo'limi", "description": "Moliyaviy operatsiyalar va hisobotlar"},
            {"name": "Ombor bo'limi", "description": "Xom-ashyo va mahsulotlar ombori"},
            {"name": "Texnik xizmat bo'limi", "description": "Uskunalar texnik ta'minoti"},
            {"name": "Boshqaruv bo'limi", "description": "Umumiy boshqaruv va administrator"},
        ]
        
        created_departments = []
        for dept_data in departments_data:
            existing = db.query(Department).filter(
                Department.name == dept_data["name"]
            ).first()
            
            if not existing:
                dept = Department(**dept_data)
                db.add(dept)
                db.commit()
                db.refresh(dept)
                created_departments.append(dept)
            else:
                created_departments.append(existing)
        
        print(f"✅ {len(departments_data)} ta bo'lim yaratildi\n")
        
        # Employees
        print("📝 Xodimlar yaratilmoqda...")
        employees_data = [
            {
                "first_name": "Sardor",
                "last_name": "Karimov",
                "phone": "+998901234567",
                "email": "sardor.k@spromax.uz",
                "department": created_departments[5],  # Boshqaruv
                "position": "Direktor",
                "hire_date": date(2020, 1, 15),
                "salary": Decimal("15000000")
            },
            {
                "first_name": "Malika",
                "last_name": "Rahimova",
                "phone": "+998901234568",
                "email": "malika.r@spromax.uz",
                "department": created_departments[2],  # Moliya
                "position": "Bosh hisobchi",
                "hire_date": date(2020, 3, 10),
                "salary": Decimal("8000000")
            },
            {
                "first_name": "Otabek",
                "last_name": "Tursunov",
                "phone": "+998901234569",
                "department": created_departments[0],  # Ishlab chiqarish
                "position": "Ishlab chiqarish bo'limi boshlig'i",
                "hire_date": date(2021, 6, 1),
                "salary": Decimal("7000000")
            },
            {
                "first_name": "Dilnoza",
                "last_name": "Usmonova",
                "phone": "+998901234570",
                "department": created_departments[1],  # Savdo
                "position": "Savdo menedjeri",
                "hire_date": date(2022, 2, 15),
                "salary": Decimal("5000000")
            },
            {
                "first_name": "Jasur",
                "last_name": "Normatov",
                "phone": "+998901234571",
                "department": created_departments[3],  # Ombor
                "position": "Omborchi",
                "hire_date": date(2021, 9, 20),
                "salary": Decimal("4000000")
            },
        ]
        
        for emp_data in employees_data:
            existing = db.query(Employee).filter(
                Employee.phone == emp_data["phone"]
            ).first()
            
            if not existing:
                employee = Employee(
                    first_name=emp_data["first_name"],
                    last_name=emp_data["last_name"],
                    phone=emp_data["phone"],
                    email=emp_data.get("email"),
                    department_id=emp_data["department"].id,
                    position=emp_data["position"],
                    hire_date=emp_data["hire_date"],
                    salary=emp_data["salary"],
                    employment_status="active"
                )
                db.add(employee)
        
        db.commit()
        print(f"✅ {len(employees_data)} ta xodim yaratildi\n")
        
        print("✅ HR seed data tugadi!\n")
        
    except Exception as e:
        print(f"\n❌ Xatolik: {e}\n")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_hr_data()