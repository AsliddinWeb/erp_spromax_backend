from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.schemas.sales import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerStatistics,
    OrderCreate, OrderUpdate, OrderResponse,
    PaymentCreate, PaymentResponse,
    SalesStatistics
)
from app.services.sales_service import SalesService
from app.dependencies import get_current_user, require_permission, require_admin
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
    service = SalesService(db)
    return service.create_customer(customer_data)


@router.get("/customers")
async def get_customers(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        page: int = Query(1, ge=1),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    """Barcha mijozlar — total_orders va total_spent bilan"""
    service = SalesService(db)
    actual_skip = (page - 1) * limit if page > 1 else skip
    result = service.get_all_customers(skip=actual_skip, limit=limit)
    return {"items": result["customers"], "total": result["total"], "page": page, "limit": limit}


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
        customer_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    service = SalesService(db)
    return service.get_customer(customer_id)


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
        customer_id: UUID,
        customer_data: CustomerUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_SALES))
):
    service = SalesService(db)
    return service.update_customer(customer_id, customer_data)


@router.delete("/customers/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer(
        customer_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    service = SalesService(db)
    service.delete_customer(customer_id)
    return {"message": "Mijoz o'chirildi"}


@router.get("/customers/{customer_id}/statistics", response_model=CustomerStatistics)
async def get_customer_statistics(
        customer_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    service = SalesService(db)
    return service.get_customer_statistics(customer_id)


# ============ ORDER ENDPOINTS ============

@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
        order_data: OrderCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_SALES))
):
    service = SalesService(db)
    return service.create_order(order_data, current_user.id)


@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        page: int = Query(1, ge=1),
        payment_status: Optional[str] = Query(None),
        delivery_status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    """Barcha buyurtmalar"""
    service = SalesService(db)
    actual_skip = (page - 1) * limit if page > 1 else skip
    return service.get_all_orders(
        skip=actual_skip, limit=limit,
        payment_status=payment_status,
        delivery_status=delivery_status
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
        order_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    service = SalesService(db)
    return service.get_order(order_id)


@router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
        order_id: UUID,
        order_data: OrderUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_SALES))
):
    service = SalesService(db)
    return service.update_order(order_id, order_data)


@router.delete("/orders/{order_id}", status_code=status.HTTP_200_OK)
async def delete_order(
        order_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
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
    service = SalesService(db)
    return service.get_customer_orders(customer_id, skip=skip, limit=limit)


# ============ PAYMENT ENDPOINTS ============

@router.get("/payments")
async def get_all_payments(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    """Barcha to'lovlar — mijoz nomi bilan"""
    from sqlalchemy import desc
    from app.models.sales import Payment, Order, Customer

    rows = (
        db.query(Payment, Order, Customer)
        .join(Order, Payment.order_id == Order.id)
        .join(Customer, Order.customer_id == Customer.id)
        .filter(Payment.is_active == True)
        .order_by(desc(Payment.payment_date))
        .offset(skip).limit(limit).all()
    )

    result = []
    for payment, order, customer in rows:
        result.append({
            "id": str(payment.id),
            "order_id": str(payment.order_id),
            "amount": float(payment.amount),
            "payment_date": payment.payment_date,
            "payment_method": payment.payment_method,
            "transaction_id": payment.transaction_id,
            "notes": payment.notes,
            "received_by": str(payment.received_by),
            "customer_name": customer.name,
            "customer_id": str(customer.id),
            "created_at": payment.created_at,
        })

    total = db.query(Payment).filter(Payment.is_active == True).count()
    return {"items": result, "total": total}


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
        payment_data: PaymentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_SALES))
):
    service = SalesService(db)
    return service.create_payment(payment_data, current_user.id)


@router.delete("/payments/{payment_id}", status_code=status.HTTP_200_OK)
async def delete_payment(
        payment_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """To'lovni o'chirish (faqat admin)"""
    service = SalesService(db)
    service.delete_payment(payment_id)
    return {"message": "To'lov o'chirildi"}


@router.get("/orders/{order_id}/payments", response_model=List[PaymentResponse])
async def get_order_payments(
        order_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    service = SalesService(db)
    return service.get_order_payments(order_id)


# ============ STATISTICS ENDPOINT ============

@router.get("/statistics", response_model=SalesStatistics)
async def get_statistics(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_SALES))
):
    service = SalesService(db)
    return service.get_sales_statistics()