import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.user import User, Role, Permission
from app.core.security import get_password_hash
from app.core.constants import UserRole, PermissionType


def create_permissions(db):
    """Permissionlarni yaratish"""
    print("📝 Permissionlar yaratilmoqda...")
    
    permissions = [
        Permission(name=p.value, description=p.value) 
        for p in PermissionType
    ]
    
    for perm in permissions:
        existing = db.query(Permission).filter(Permission.name == perm.name).first()
        if not existing:
            db.add(perm)
    
    db.commit()
    print(f"✅ {len(list(PermissionType))} ta permission yaratildi")


def create_roles(db):
    """Rollarni yaratish"""
    print("📝 Rollar yaratilmoqda...")
    
    from app.core.permissions import ROLE_PERMISSIONS
    
    for role_name, perm_types in ROLE_PERMISSIONS.items():
        existing_role = db.query(Role).filter(Role.name == role_name.value).first()
        
        if not existing_role:
            new_role = Role(
                name=role_name.value,
                description=f"{role_name.value} role"
            )
            
            # Permissionlarni qo'shish
            for perm_type in perm_types:
                perm = db.query(Permission).filter(
                    Permission.name == perm_type.value
                ).first()
                if perm:
                    new_role.permissions.append(perm)
            
            db.add(new_role)
            print(f"  ✅ {role_name.value} role yaratildi")
    
    db.commit()
    print(f"✅ {len(ROLE_PERMISSIONS)} ta role yaratildi")


def create_superadmin(db):
    """Superadmin yaratish"""
    print("📝 Superadmin yaratilmoqda...")
    
    superadmin_role = db.query(Role).filter(
        Role.name == UserRole.SUPERADMIN.value
    ).first()
    
    if not superadmin_role:
        print("❌ Superadmin role topilmadi")
        return
    
    existing_admin = db.query(User).filter(User.username == "admin").first()
    
    if not existing_admin:
        admin = User(
            username="admin",
            email="admin@spromax.uz",
            full_name="System Administrator",
            hashed_password=get_password_hash("Admin123!"),
            role_id=superadmin_role.id
        )
        db.add(admin)
        db.commit()
        print("✅ Superadmin yaratildi")
        print("   📧 Email:    admin@spromax.uz")
        print("   👤 Username: admin")
        print("   🔑 Password: Admin123!")
    else:
        print("ℹ️  Superadmin allaqachon mavjud")


def seed_data():
    """Barcha seed data"""
    db = SessionLocal()
    
    try:
        print("\n🌱 Seed data boshlandi...\n")
        create_permissions(db)
        print()
        create_roles(db)
        print()
        create_superadmin(db)
        print("\n✅ Seed data tugadi!\n")
        print("=" * 60)
        print("📝 LOGIN CREDENTIALS:")
        print("=" * 60)
        print("   Email:    admin@spromax.uz")
        print("   Username: admin")
        print("   Password: Admin123!")
        print("=" * 60)
        print("\n💡 Login qilish uchun username='admin' ishlatiladi\n")
        
    except Exception as e:
        print(f"\n❌ Xatolik: {e}\n")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()