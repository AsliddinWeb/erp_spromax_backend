from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app.models.user import User


class TransactionCategory(BaseModel):
    """Moliyaviy operatsiya kategoriyalari jadvali"""
    __tablename__ = "transaction_categories"

    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    category_type = Column(String(20), nullable=False)  # income, expense

    # Relationships
    transactions = relationship("FinancialTransaction", back_populates="category")

    def __repr__(self):
        return f"<TransactionCategory {self.name}>"


class FinancialTransaction(BaseModel):
    """Moliyaviy operatsiyalar jadvali"""
    __tablename__ = "financial_transactions"

    transaction_date = Column(DateTime, nullable=False)
    transaction_type = Column(String(20), nullable=False)  # income, expense
    amount = Column(Numeric(12, 2), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey('transaction_categories.id'), nullable=False)
    description = Column(Text, nullable=True)
    reference_type = Column(String(50), nullable=True)  # sales_payment, salary_payment, warehouse_receipt, etc.
    reference_id = Column(UUID(as_uuid=True), nullable=True)  # ID of related record
    is_auto = Column(Boolean, default=False, nullable=False)  # Avtomatik yaratilganmi

    # Foreign Keys
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Relationships
    category = relationship("TransactionCategory", back_populates="transactions")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<FinancialTransaction {self.transaction_type}: {self.amount}>"