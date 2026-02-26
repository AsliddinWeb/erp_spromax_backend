from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from app.database import get_db
from app.schemas.finance import (
    # Category
    TransactionCategoryCreate,
    TransactionCategoryUpdate,
    TransactionCategoryResponse,
    # Transaction
    FinancialTransactionCreate,
    FinancialTransactionUpdate,
    FinancialTransactionResponse,
    # Reports
    ProfitAndLossReport,
    CashFlowReport,
    BalanceSheet,
    FinanceStatistics
)
from app.services.finance_service import FinanceService
from app.dependencies import get_current_user, require_permission
from app.models.user import User
from app.core.constants import PermissionType

router = APIRouter(prefix="/finance", tags=["Finance"])


# ============ CATEGORY ENDPOINTS ============

@router.post("/categories", response_model=TransactionCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
        category_data: TransactionCategoryCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_FINANCE))
):
    """Yangi kategoriya yaratish"""
    service = FinanceService(db)
    return service.create_category(category_data)


@router.get("/categories", response_model=List[TransactionCategoryResponse])
async def get_categories(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        category_type: Optional[str] = Query(None, pattern="^(income|expense)$"),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_FINANCE))
):
    """Kategoriyalar ro'yxati"""
    service = FinanceService(db)

    if category_type:
        return service.get_categories_by_type(category_type)

    return service.get_all_categories(skip=skip, limit=limit)


@router.get("/categories/{category_id}", response_model=TransactionCategoryResponse)
async def get_category(
        category_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_FINANCE))
):
    """Bitta kategoriya"""
    service = FinanceService(db)
    return service.get_category(category_id)


@router.put("/categories/{category_id}", response_model=TransactionCategoryResponse)
async def update_category(
        category_id: UUID,
        category_data: TransactionCategoryUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_FINANCE))
):
    """Kategoriya yangilash"""
    service = FinanceService(db)
    return service.update_category(category_id, category_data)


@router.delete("/categories/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(
        category_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_FINANCE))
):
    """Kategoriya o'chirish"""
    service = FinanceService(db)
    service.delete_category(category_id)
    return {"message": "Kategoriya o'chirildi"}


# ============ TRANSACTION ENDPOINTS ============

@router.post("/transactions", response_model=FinancialTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
        transaction_data: FinancialTransactionCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_FINANCE))
):
    """
    Yangi tranzaksiya yaratish

    Daromad yoki xarajat operatsiyasini qo'lda kiritish.
    """
    service = FinanceService(db)
    return service.create_transaction(transaction_data, current_user.id)


@router.get("/transactions", response_model=List[FinancialTransactionResponse])
async def get_transactions(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        transaction_type: Optional[str] = Query(None, pattern="^(income|expense)$"),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None),
        reference_type: Optional[str] = Query(None),
        is_auto: Optional[bool] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_FINANCE))
):
    """
    Tranzaksiyalar ro'yxati

    Filtrlash: turi, sana oralig'i, manba turi, avtomatik/qo'lda
    """
    service = FinanceService(db)
    return service.get_all_transactions(
        skip=skip,
        limit=limit,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        reference_type=reference_type,
        is_auto=is_auto
    )


@router.get("/transactions/{transaction_id}", response_model=FinancialTransactionResponse)
async def get_transaction(
        transaction_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_FINANCE))
):
    """Bitta tranzaksiya"""
    service = FinanceService(db)
    return service.get_transaction(transaction_id)


@router.put("/transactions/{transaction_id}", response_model=FinancialTransactionResponse)
async def update_transaction(
        transaction_id: UUID,
        transaction_data: FinancialTransactionUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_FINANCE))
):
    """Tranzaksiya yangilash"""
    service = FinanceService(db)
    return service.update_transaction(transaction_id, transaction_data)


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_200_OK)
async def delete_transaction(
        transaction_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.WRITE_FINANCE))
):
    """Tranzaksiya o'chirish"""
    service = FinanceService(db)
    service.delete_transaction(transaction_id)
    return {"message": "Tranzaksiya o'chirildi"}


# ============ REPORT ENDPOINTS ============

@router.get("/reports/pl", response_model=ProfitAndLossReport)
async def get_profit_and_loss(
        start_date: datetime = Query(...),
        end_date: datetime = Query(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_FINANCE))
):
    """
    Daromad-Xarajat (P&L) hisoboti

    Belgilangan davr uchun umumiy daromad, xarajat va foyda.
    """
    service = FinanceService(db)
    return service.get_profit_and_loss(start_date, end_date)


@router.get("/reports/cashflow", response_model=CashFlowReport)
async def get_cash_flow(
        start_date: datetime = Query(...),
        end_date: datetime = Query(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_FINANCE))
):
    """
    Pul oqimi (Cash Flow) hisoboti

    Davr uchun pul kirim-chiqimi.
    """
    service = FinanceService(db)
    return service.get_cash_flow(start_date, end_date)


@router.get("/reports/balance", response_model=BalanceSheet)
async def get_balance_sheet(
        report_date: datetime = Query(default_factory=datetime.utcnow),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_FINANCE))
):
    """
    Balans hisoboti

    Aktivlar, passivlar va kapital (soddalashtirilgan).
    """
    service = FinanceService(db)
    return service.get_balance_sheet(report_date)


# ============ STATISTICS ENDPOINT ============

@router.get("/statistics", response_model=FinanceStatistics)
async def get_statistics(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_permission(PermissionType.READ_FINANCE))
):
    """Moliyaviy statistika"""
    service = FinanceService(db)
    return service.get_statistics()