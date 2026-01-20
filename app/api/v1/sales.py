from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.schemas.sales import (
    # Customer
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerStatistics,
    # Order
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    # Payment
    PaymentCreate,
    PaymentResponse,
    # Statistics
    SalesStatistics
)
from app.services.sales_service import SalesService
from app.dependencies import get_current_user, require_permission
from app.models.user import User
from app.core.constants import PermissionType

router = APIRouter(prefix="/sales", tags=["Sales"])


# ============ CUSTOMER ENDPOINTS ============

@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.WRITE_SALES))
):
    """Yangi mijoz qo'shish"""
    service = SalesService(db)
    return service.create_customer(customer_data)


@router.get("/customers", response_model=List[CustomerResponse])
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    """Barcha mijozlar ro'yxati"""
    service = SalesService(db)
    return service.get_all_customers(skip=skip, limit=limit)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    """Bitta mijoz ma'lumotlari"""
    service = SalesService(db)
    return service.get_customer(customer_id)


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.WRITE_SALES))
):
    """Mijoz ma'lumotlarini yangilash"""
    service = SalesService(db)
    return service.update_customer(customer_id, customer_data)


@router.delete("/customers/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.WRITE_SALES))
):
    """Mijozni o'chirish"""
    service = SalesService(db)
    service.delete_customer(customer_id)
    return {"message": "Mijoz o'chirildi"}


@router.get("/customers/{customer_id}/statistics", response_model=CustomerStatistics)
async def get_customer_statistics(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    """Mijoz statistikasi"""
    service = SalesService(db)
    return service.get_customer_statistics(customer_id)


# ============ ORDER ENDPOINTS ============

@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.WRITE_SALES))
):
    """
    Yangi buyurtma yaratish
    
    Mijozdan buyurtma qabul qilish va mahsulotlarni rezerv qilish.
    """
    service = SalesService(db)
    return service.create_order(order_data, current_user.id)


@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    payment_status: Optional[str] = Query(None),
    delivery_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    """Barcha buyurtmalar ro'yxati"""
    service = SalesService(db)
    return service.get_all_orders(
        skip=skip,
        limit=limit,
        payment_status=payment_status,
        delivery_status=delivery_status
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    """Bitta buyurtma ma'lumotlari"""
    service = SalesService(db)
    return service.get_order(order_id)


@router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    order_data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.WRITE_SALES))
):
    """
    Buyurtma yangilash
    
    Delivery status o'zgarishi bilan stock avtomatik yangilanadi.
    """
    service = SalesService(db)
    return service.update_order(order_id, order_data)


@router.delete("/orders/{order_id}", status_code=status.HTTP_200_OK)
async def delete_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.WRITE_SALES))
):
    """Buyurtmani bekor qilish"""
    service = SalesService(db)
    service.delete_order(order_id)
    return {"message": "Buyurtma bekor qilindi"}


@router.get("/customers/{customer_id}/orders", response_model=List[OrderResponse])
async def get_customer_orders(
    customer_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    """Mijoz buyurtmalari"""
    service = SalesService(db)
    return service.get_customer_orders(customer_id, skip=skip, limit=limit)


# ============ PAYMENT ENDPOINTS ============

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.WRITE_SALES))
):
    """
    To'lov qo'shish
    
    Mijoz to'lov qilganda buyurtma payment_status avtomatik yangilanadi.
    """
    service = SalesService(db)
    return service.create_payment(payment_data, current_user.id)


@router.get("/orders/{order_id}/payments", response_model=List[PaymentResponse])
async def get_order_payments(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    """Buyurtma to'lovlari tarixi"""
    service = SalesService(db)
    return service.get_order_payments(order_id)


# ============ STATISTICS ENDPOINT ============

@router.get("/statistics", response_model=SalesStatistics)
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    """Sotuv statistikasi"""
    service = SalesService(db)
    return service.get_sales_statistics()