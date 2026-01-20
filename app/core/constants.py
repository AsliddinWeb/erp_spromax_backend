from enum import Enum


class UserRole(str, Enum):
    """Foydalanuvchi rollari"""
    SUPERADMIN = "superadmin"
    DIRECTOR = "director"
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    WAREHOUSE_MANAGER = "warehouse_manager"
    OPERATOR = "operator"
    SALES_MANAGER = "sales_manager"
    HR_MANAGER = "hr_manager"
    MAINTENANCE = "maintenance"


class PermissionType(str, Enum):
    """Ruxsat turlari"""
    # User management
    MANAGE_USERS = "manage:users"
    
    # Warehouse
    READ_WAREHOUSE = "read:warehouse"
    WRITE_WAREHOUSE = "write:warehouse"
    APPROVE_MATERIAL_REQUEST = "approve:material_request"
    
    # Production
    READ_PRODUCTION = "read:production"
    WRITE_PRODUCTION = "write:production"
    
    # Sales
    READ_SALES = "read:sales"
    WRITE_SALES = "write:sales"
    
    # Finance
    READ_FINANCE = "read:finance"
    WRITE_FINANCE = "write:finance"
    
    # HR
    READ_HR = "read:hr"
    WRITE_HR = "write:hr"
    
    # Maintenance
    READ_MAINTENANCE = "read:maintenance"
    WRITE_MAINTENANCE = "write:maintenance"
    
    # Analytics
    READ_ANALYTICS = "read:analytics"


class RequestStatus(str, Enum):
    """So'rov statuslari"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTIALLY_APPROVED = "partially_approved"


class ShiftStatus(str, Enum):
    """Smena statuslari"""
    ACTIVE = "active"
    COMPLETED = "completed"


class OrderStatus(str, Enum):
    """Buyurtma statuslari"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    """To'lov statuslari"""
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"


class TransactionType(str, Enum):
    """Tranzaksiya turlari"""
    INCOME = "income"
    EXPENSE = "expense"


class MaintenanceStatus(str, Enum):
    """Texnik xizmat statuslari"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class MaintenancePriority(str, Enum):
    """Texnik xizmat prioriteti"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"