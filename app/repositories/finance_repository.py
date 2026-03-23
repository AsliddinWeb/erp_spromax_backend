from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from decimal import Decimal
from app.utils.datetime_utils import get_today_start, get_month_start
from uuid import UUID
from app.models.finance import TransactionCategory, FinancialTransaction
from app.repositories.base import BaseRepository


class TransactionCategoryRepository(BaseRepository[TransactionCategory]):
    def __init__(self, db: Session):
        super().__init__(TransactionCategory, db)

    def get_by_name(self, name: str) -> Optional[TransactionCategory]:
        """Nom bo'yicha kategoriya topish"""
        return self.db.query(TransactionCategory).filter(
            TransactionCategory.name == name,
            TransactionCategory.is_active == True
        ).first()

    def get_by_type(self, category_type: str) -> List[TransactionCategory]:
        """Turi bo'yicha kategoriyalar"""
        return self.db.query(TransactionCategory).filter(
            TransactionCategory.category_type == category_type,
            TransactionCategory.is_active == True
        ).all()


class FinancialTransactionRepository(BaseRepository[FinancialTransaction]):
    def __init__(self, db: Session):
        super().__init__(FinancialTransaction, db)

    def get_with_relations(self, transaction_id: UUID) -> Optional[FinancialTransaction]:
        """Relationships bilan tranzaksiya"""
        return self.db.query(FinancialTransaction).options(
            joinedload(FinancialTransaction.category),
            joinedload(FinancialTransaction.creator)
        ).filter(
            FinancialTransaction.id == transaction_id,
            FinancialTransaction.is_active == True
        ).first()

    def get_all_with_relations(
            self,
            skip: int = 0,
            limit: int = 100,
            transaction_type: Optional[str] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            reference_type: Optional[str] = None,
            is_auto: Optional[bool] = None
    ) -> List[FinancialTransaction]:
        """Barcha tranzaksiyalar"""
        query = self.db.query(FinancialTransaction).options(
            joinedload(FinancialTransaction.category)
        ).filter(FinancialTransaction.is_active == True)

        if transaction_type:
            query = query.filter(FinancialTransaction.transaction_type == transaction_type)

        if start_date:
            query = query.filter(FinancialTransaction.transaction_date >= start_date)

        if end_date:
            query = query.filter(FinancialTransaction.transaction_date <= end_date)

        if reference_type is not None:
            query = query.filter(FinancialTransaction.reference_type == reference_type)

        if is_auto is not None:
            query = query.filter(FinancialTransaction.is_auto == is_auto)

        return query.order_by(desc(FinancialTransaction.transaction_date)).offset(skip).limit(limit).all()

    def get_total_by_type(
            self,
            transaction_type: str,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Decimal:
        """Turi bo'yicha umumiy summa"""
        query = self.db.query(func.sum(FinancialTransaction.amount)).filter(
            FinancialTransaction.transaction_type == transaction_type,
            FinancialTransaction.is_active == True
        )

        if start_date:
            query = query.filter(FinancialTransaction.transaction_date >= start_date)

        if end_date:
            query = query.filter(FinancialTransaction.transaction_date <= end_date)

        result = query.scalar()
        return result or Decimal("0")

    def get_by_category(
            self,
            category_id: UUID,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[FinancialTransaction]:
        """Kategoriya bo'yicha tranzaksiyalar"""
        query = self.db.query(FinancialTransaction).filter(
            FinancialTransaction.category_id == category_id,
            FinancialTransaction.is_active == True
        )

        if start_date:
            query = query.filter(FinancialTransaction.transaction_date >= start_date)

        if end_date:
            query = query.filter(FinancialTransaction.transaction_date <= end_date)

        return query.order_by(desc(FinancialTransaction.transaction_date)).all()

    def get_income_by_category(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Kategoriya bo'yicha daromad"""
        query = self.db.query(
            TransactionCategory.name,
            func.sum(FinancialTransaction.amount).label('total')
        ).join(
            FinancialTransaction.category
        ).filter(
            FinancialTransaction.transaction_type == 'income',
            FinancialTransaction.is_active == True
        )

        if start_date:
            query = query.filter(FinancialTransaction.transaction_date >= start_date)

        if end_date:
            query = query.filter(FinancialTransaction.transaction_date <= end_date)

        results = query.group_by(TransactionCategory.name).order_by(desc('total')).all()

        return [{"category": r.name, "amount": r.total} for r in results]

    def get_expense_by_category(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Kategoriya bo'yicha xarajat"""
        query = self.db.query(
            TransactionCategory.name,
            func.sum(FinancialTransaction.amount).label('total')
        ).join(
            FinancialTransaction.category
        ).filter(
            FinancialTransaction.transaction_type == 'expense',
            FinancialTransaction.is_active == True
        )

        if start_date:
            query = query.filter(FinancialTransaction.transaction_date >= start_date)

        if end_date:
            query = query.filter(FinancialTransaction.transaction_date <= end_date)

        results = query.group_by(TransactionCategory.name).order_by(desc('total')).all()

        return [{"category": r.name, "amount": r.total} for r in results]

    def get_today_total(self, transaction_type: str) -> Decimal:
        """Bugungi umumiy summa"""
        today_start = get_today_start()
        return self.get_total_by_type(transaction_type, start_date=today_start)

    def get_month_total(self, transaction_type: str) -> Decimal:
        """Oy boshidan umumiy summa"""
        month_start = get_month_start()
        return self.get_total_by_type(transaction_type, start_date=month_start)