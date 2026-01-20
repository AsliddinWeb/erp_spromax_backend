from typing import List
from app.core.constants import UserRole, PermissionType


# Role va permission mapping
ROLE_PERMISSIONS = {
    UserRole.SUPERADMIN: [
        # Barcha ruxsatlar
        PermissionType.MANAGE_USERS,
        PermissionType.READ_WAREHOUSE,
        PermissionType.WRITE_WAREHOUSE,
        PermissionType.APPROVE_MATERIAL_REQUEST,
        PermissionType.READ_PRODUCTION,
        PermissionType.WRITE_PRODUCTION,
        PermissionType.READ_SALES,
        PermissionType.WRITE_SALES,
        PermissionType.READ_FINANCE,
        PermissionType.WRITE_FINANCE,
        PermissionType.READ_HR,
        PermissionType.WRITE_HR,
        PermissionType.READ_MAINTENANCE,
        PermissionType.WRITE_MAINTENANCE,
        PermissionType.READ_ANALYTICS,
    ],
    
    UserRole.DIRECTOR: [
        PermissionType.READ_WAREHOUSE,
        PermissionType.READ_PRODUCTION,
        PermissionType.READ_SALES,
        PermissionType.READ_FINANCE,
        PermissionType.READ_HR,
        PermissionType.READ_MAINTENANCE,
        PermissionType.READ_ANALYTICS,
    ],
    
    UserRole.ADMIN: [
        PermissionType.MANAGE_USERS,
        PermissionType.READ_WAREHOUSE,
        PermissionType.READ_PRODUCTION,
        PermissionType.READ_SALES,
        PermissionType.READ_HR,
    ],
    
    UserRole.ACCOUNTANT: [
        PermissionType.READ_FINANCE,
        PermissionType.WRITE_FINANCE,
        PermissionType.READ_SALES,
        PermissionType.READ_WAREHOUSE,
    ],
    
    UserRole.WAREHOUSE_MANAGER: [
        PermissionType.READ_WAREHOUSE,
        PermissionType.WRITE_WAREHOUSE,
        PermissionType.APPROVE_MATERIAL_REQUEST,
    ],
    
    UserRole.OPERATOR: [
        PermissionType.READ_PRODUCTION,
        PermissionType.WRITE_PRODUCTION,
        PermissionType.READ_WAREHOUSE,
    ],
    
    UserRole.SALES_MANAGER: [
        PermissionType.READ_SALES,
        PermissionType.WRITE_SALES,
        PermissionType.READ_WAREHOUSE,
    ],
    
    UserRole.HR_MANAGER: [
        PermissionType.READ_HR,
        PermissionType.WRITE_HR,
    ],
    
    UserRole.MAINTENANCE: [
        PermissionType.READ_MAINTENANCE,
        PermissionType.WRITE_MAINTENANCE,
    ],
}


def get_role_permissions(role: UserRole) -> List[PermissionType]:
    """Role bo'yicha ruxsatlarni olish"""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(role: UserRole, permission: PermissionType) -> bool:
    """Role ushbu ruxsatga ega yoki yo'qligini tekshirish"""
    role_perms = get_role_permissions(role)
    return permission in role_perms