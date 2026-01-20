from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
from app.models.finance import TransactionCategory, FinancialTransaction
from app.schemas.finance import (
    TransactionCategoryCreate,
    TransactionCategoryUpdate,
    FinancialTransactionCreate,
    FinancialTransactionUpdate,
    ProfitAndLossReport,
    CashFlowReport,
    BalanceSheet,
    FinanceStatistics
)
from app.repositories.finance_repository import (
    TransactionCategoryRepository,
    FinancialTransactionRepository
)
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException
)


class FinanceService:
    def __init__(self, db: Session):
        self.db = db
        self.category_repo = TransactionCategoryRepository(db)
        self.transaction_repo = FinancialTransactionRepository(db)
    
    # ============ TRANSACTION CATEGORY METHODS ============
    
    def create_category(self, category_data: TransactionCategoryCreate) -> TransactionCategory:
        """Yangi kategoriya yaratish"""
        existing = self.category_repo.get_by_name(category_data.name)
        if existing:
            raise ConflictException(detail=f"'{category_data.name}' nomli kategoriya mavjud")
        
        new_category = TransactionCategory(**category_data.model_dump())
        return self.category_repo.create(new_category)
    
    def get_category(self, category_id: UUID) -> TransactionCategory:
        """Kategoriya olish"""
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise NotFoundException(detail="Kategoriya topilmadi")
        return category
    
    def get_all_categories(self, skip: int = 0, limit: int = 100) -> List[TransactionCategory]:
        """Barcha kategoriyalar"""
        return self.category_repo.get_all(skip=skip, limit=limit)
    
    def get_categories_by_type(self, category_type: str) -> List[TransactionCategory]:
        """Turi bo'yicha kategoriyalar"""
        return self.category_repo.get_by_type(category_type)
    
    def update_category(self, category_id: UUID, category_data: TransactionCategoryUpdate) -> TransactionCategory:
        """Kategoriya yangilash"""
        category = self.get_category(category_id)
        
        if category_data.name and category_data.name != category.name:
            existing = self.category_repo.get_by_name(category_data.name)
            if existing:
                raise ConflictException(detail=f"'{category_data.name}' nomli kategoriya mavjud")
        
        update_data = category_data.model_dump(exclude_unset=True)
        return self.category_repo.update(category, update_data)
    
    def delete_category(self, category_id: UUID) -> bool:
        """Kategoriya o'chirish"""
        return self.category_repo.delete(category_id)
    
    # ============ FINANCIAL TRANSACTION METHODS ============
    
    def create_transaction(
        self,
        transaction_data: FinancialTransactionCreate,
        user_id: UUID
    ) -> FinancialTransaction:
        """Yangi tranzaksiya yaratish"""
        # Kategoriya tekshirish
        category = self.get_category(transaction_data.category_id)
        
        # Transaction type va category type mos kelishini tekshirish
        if transaction_data.transaction_type != category.category_type:
            raise BadRequestException(
                detail=f"Tranzaksiya turi kategoriya turi bilan mos kelmaydi"
            )
        
        new_transaction = FinancialTransaction(
            transaction_date=transaction_data.transaction_date,
            transaction_type=transaction_data.transaction_type,
            amount=transaction_data.amount,
            category_id=transaction_data.category_id,
            description=transaction_data.description,
            reference_type=transaction_data.reference_type,
            reference_id=transaction_data.reference_id,
            created_by=user_id
        )
        
        return self.transaction_repo.create(new_transaction)
    
    def get_transaction(self, transaction_id: UUID) -> FinancialTransaction:
        """Tranzaksiya olish"""
        transaction = self.transaction_repo.get_with_relations(transaction_id)
        if not transaction:
            raise NotFoundException(detail="Tranzaksiya topilmadi")
        return transaction
    
    def get_all_transactions(
        self,
        skip: int = 0,
        limit: int = 100,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[FinancialTransaction]:
        """Barcha tranzaksiyalar"""
        return self.transaction_repo.get_all_with_relations(
            skip=skip,
            limit=limit,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date
        )
    
    def update_transaction(
        self,
        transaction_id: UUID,
        transaction_data: FinancialTransactionUpdate
    ) -> FinancialTransaction:
        """Tranzaksiya yangilash"""
        transaction = self.get_transaction(transaction_id)
        
        # Agar category_id o'zgarsa, type'ni tekshirish
        if transaction_data.category_id:
            category = self.get_category(transaction_data.category_id)
            if transaction.transaction_type != category.category_type:
                raise BadRequestException(
                    detail="Yangi kategoriya tranzaksiya turi bilan mos kelmaydi"
                )
        
        update_data = transaction_data.model_dump(exclude_unset=True)
        return self.transaction_repo.update(transaction, update_data)
    
    def delete_transaction(self, transaction_id: UUID) -> bool:
        """Tranzaksiya o'chirish"""
        return self.transaction_repo.delete(transaction_id)
    
    # ============ AUTOMATIC TRANSACTION CREATION ============
    
    def create_automatic_transaction(
        self,
        transaction_type: str,
        amount: Decimal,
        category_name: str,
        description: str,
        reference_type: str,
        reference_id: UUID,
        user_id: UUID
    ) -> Optional[FinancialTransaction]:
        """
        Avtomatik tranzaksiya yaratish (boshqa modullardan)
        
        Masalan: Buyurtma to'langanda avtomatik income yaratish
        """
        # Kategoriya topish
        category = self.category_repo.get_by_name(category_name)
        if not category:
            # Agar kategoriya yo'q bo'lsa, None qaytaramiz
            return None
        
        new_transaction = FinancialTransaction(
            transaction_date=datetime.utcnow(),
            transaction_type=transaction_type,
            amount=amount,
            category_id=category.id,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
            created_by=user_id
        )
        
        return self.transaction_repo.create(new_transaction)
    
    # ============ REPORT METHODS ============
    
    def get_profit_and_loss(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> ProfitAndLossReport:
        """Daromad-Xarajat (P&L) hisoboti"""
        total_income = self.transaction_repo.get_total_by_type(
            'income',
            start_date=start_date,
            end_date=end_date
        )
        
        total_expense = self.transaction_repo.get_total_by_type(
            'expense',
            start_date=start_date,
            end_date=end_date
        )
        
        net_profit = total_income - total_expense
        
        income_by_category = self.transaction_repo.get_income_by_category(
            start_date=start_date,
            end_date=end_date
        )
        
        expense_by_category = self.transaction_repo.get_expense_by_category(
            start_date=start_date,
            end_date=end_date
        )
        
        return ProfitAndLossReport(
            period_start=start_date,
            period_end=end_date,
            total_income=total_income,
            total_expense=total_expense,
            net_profit=net_profit,
            income_by_category=income_by_category,
            expense_by_category=expense_by_category
        )
    
    def get_cash_flow(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> CashFlowReport:
        """Pul oqimi hisoboti"""
        # Soddalashtirilgan versiya
        total_inflow = self.transaction_repo.get_total_by_type(
            'income',
            start_date=start_date,
            end_date=end_date
        )
        
        total_outflow = self.transaction_repo.get_total_by_type(
            'expense',
            start_date=start_date,
            end_date=end_date
        )
        
        opening_balance = Decimal("0")  # TODO: Implement proper opening balance
        closing_balance = opening_balance + total_inflow - total_outflow
        
        return CashFlowReport(
            period_start=start_date,
            period_end=end_date,
            opening_balance=opening_balance,
            total_inflow=total_inflow,
            total_outflow=total_outflow,
            closing_balance=closing_balance,
            cash_flow_by_month=[]  # TODO: Implement monthly breakdown
        )
    
    def get_balance_sheet(self, report_date: datetime) -> BalanceSheet:
        """Balans hisoboti (soddalashtirilgan)"""
        # Real ERP da Assets, Liabilities, Equity hisoblash kerak
        # Bu soddalashtirilgan versiya
        
        total_income = self.transaction_repo.get_total_by_type('income')
        total_expense = self.transaction_repo.get_total_by_type('expense')
        
        total_equity = total_income - total_expense
        total_assets = total_equity  # Soddalashtirilgan
        total_liabilities = Decimal("0")  # Soddalashtirilgan
        
        return BalanceSheet(
            report_date=report_date,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity
        )
    
    # ============ STATISTICS METHODS ============
    
    def get_statistics(self) -> FinanceStatistics:
        """Moliyaviy statistika"""
        total_transactions = self.transaction_repo.count()
        
        total_income = self.transaction_repo.get_total_by_type('income')
        total_expense = self.transaction_repo.get_total_by_type('expense')
        net_profit = total_income - total_expense
        
        income_today = self.transaction_repo.get_today_total('income')
        expense_today = self.transaction_repo.get_today_total('expense')
        
        income_this_month = self.transaction_repo.get_month_total('income')
        expense_this_month = self.transaction_repo.get_month_total('expense')
        
        top_income_categories = self.transaction_repo.get_income_by_category()[:5]
        top_expense_categories = self.transaction_repo.get_expense_by_category()[:5]
        
        return FinanceStatistics(
            total_transactions=total_transactions,
            total_income=total_income,
            total_expense=total_expense,
            net_profit=net_profit,
            income_today=income_today,
            expense_today=expense_today,
            income_this_month=income_this_month,
            expense_this_month=expense_this_month,
            top_income_categories=top_income_categories,
            top_expense_categories=top_expense_categories
        )