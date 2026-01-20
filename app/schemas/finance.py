from typing import Optional, List
from pydantic import Field, field_validator
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from app.schemas.base import BaseSchema, BaseIDSchema


# ============ TRANSACTION CATEGORY SCHEMAS ============

class TransactionCategoryBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category_type: str = Field(..., pattern="^(income|expense)$")


class TransactionCategoryCreate(TransactionCategoryBase):
    pass


class TransactionCategoryUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category_type: Optional[str] = Field(None, pattern="^(income|expense)$")


class TransactionCategoryResponse(BaseIDSchema, TransactionCategoryBase):
    pass


# ============ FINANCIAL TRANSACTION SCHEMAS ============

class FinancialTransactionBase(BaseSchema):
    transaction_date: datetime
    transaction_type: str = Field(..., pattern="^(income|expense)$")
    amount: Decimal = Field(..., gt=0)
    category_id: UUID
    description: Optional[str] = None
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[UUID] = None


class FinancialTransactionCreate(FinancialTransactionBase):
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Summa musbat bo\'lishi kerak')
        return v


class FinancialTransactionUpdate(BaseSchema):
    transaction_date: Optional[datetime] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    category_id: Optional[UUID] = None
    description: Optional[str] = None


class FinancialTransactionResponse(BaseIDSchema, FinancialTransactionBase):
    created_by: UUID
    category: Optional[TransactionCategoryResponse] = None
    creator: Optional[dict] = None


# ============ REPORT SCHEMAS ============

class ProfitAndLossReport(BaseSchema):
    """Daromad-Xarajat (P&L) hisoboti"""
    period_start: datetime
    period_end: datetime
    total_income: Decimal
    total_expense: Decimal
    net_profit: Decimal
    income_by_category: List[dict] = []
    expense_by_category: List[dict] = []


class CashFlowReport(BaseSchema):
    """Pul oqimi hisoboti"""
    period_start: datetime
    period_end: datetime
    opening_balance: Decimal
    total_inflow: Decimal
    total_outflow: Decimal
    closing_balance: Decimal
    cash_flow_by_month: List[dict] = []


class BalanceSheet(BaseSchema):
    """Balans hisoboti"""
    report_date: datetime
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    # Soddalashtirilgan versiya


class FinanceStatistics(BaseSchema):
    """Moliyaviy statistika"""
    total_transactions: int
    total_income: Decimal
    total_expense: Decimal
    net_profit: Decimal
    income_today: Decimal
    expense_today: Decimal
    income_this_month: Decimal
    expense_this_month: Decimal
    top_income_categories: List[dict] = []
    top_expense_categories: List[dict] = []