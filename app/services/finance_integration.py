"""
Finance Integration Service
----------------------------
Sales, HR, Warehouse modullaridan avtomatik Transaction yaratish uchun.
"""

import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


# Bu import yo'llarni o'z loyihangizga moslang
# from app.models.finance import Transaction, TransactionCategory
# from app.models.finance import TransactionCreate


async def get_or_create_category(
        db: AsyncSession,
        name: str,
        category_type: str,  # "income" | "expense"
        TransactionCategory,
) -> object:
    """Kategoriya mavjud bo'lsa oladi, bo'lmasa yaratadi."""
    result = await db.execute(
        select(TransactionCategory).where(
            TransactionCategory.name == name,
            TransactionCategory.category_type == category_type,
            TransactionCategory.is_active == True,
        )
    )
    category = result.scalar_one_or_none()

    if not category:
        category = TransactionCategory(
            id=uuid.uuid4(),
            name=name,
            category_type=category_type,
            description=f"Avtomatik yaratilgan: {name}",
        )
        db.add(category)
        await db.flush()

    return category


async def create_auto_transaction(
        db: AsyncSession,
        transaction_type: str,
        amount: Decimal,
        description: str,
        reference_type: str,
        reference_id: uuid.UUID,
        category_name: str,
        Transaction,
        TransactionCategory,
) -> object:
    """
    Avtomatik Transaction yaratish.

    Args:
        db: Database session
        transaction_type: "income" | "expense"
        amount: Summa
        description: Tavsif
        reference_type: "sales_payment" | "salary_payment" | "warehouse_receipt"
        reference_id: Bog'liq yozuv ID
        category_name: Kategoriya nomi
        Transaction: Transaction model class
        TransactionCategory: TransactionCategory model class
    """
    category = await get_or_create_category(
        db=db,
        name=category_name,
        category_type=transaction_type,
        TransactionCategory=TransactionCategory,
    )

    transaction = Transaction(
        id=uuid.uuid4(),
        transaction_type=transaction_type,
        amount=amount,
        description=description,
        reference_type=reference_type,
        reference_id=reference_id,
        category_id=category.id,
        is_auto=True,
    )
    db.add(transaction)
    await db.flush()

    return transaction


# ─── Convenience wrappers ───────────────────────────────────────────────────

async def create_sales_transaction(
        db: AsyncSession,
        payment_id: uuid.UUID,
        amount: Decimal,
        order_id,
        Transaction,
        TransactionCategory,
) -> object:
    """Sotuv to'lovi uchun avtomatik transaction."""
    return await create_auto_transaction(
        db=db,
        transaction_type="income",
        amount=amount,
        description=f"Sotuv to'lovi — Order #{order_id}",
        reference_type="sales_payment",
        reference_id=payment_id,
        category_name="Sotuv daromadi",
        Transaction=Transaction,
        TransactionCategory=TransactionCategory,
    )


async def create_salary_transaction(
        db: AsyncSession,
        salary_payment_id: uuid.UUID,
        amount: Decimal,
        employee_full_name: str,
        Transaction,
        TransactionCategory,
) -> object:
    """Ish haqi to'lovi uchun avtomatik transaction."""
    return await create_auto_transaction(
        db=db,
        transaction_type="expense",
        amount=amount,
        description=f"Ish haqi — {employee_full_name}",
        reference_type="salary_payment",
        reference_id=salary_payment_id,
        category_name="Ish haqi xarajatlari",
        Transaction=Transaction,
        TransactionCategory=TransactionCategory,
    )


async def create_warehouse_transaction(
        db: AsyncSession,
        receipt_id: uuid.UUID,
        amount: Decimal,
        supplier_name: str,
        Transaction,
        TransactionCategory,
) -> object:
    """Xom-ashyo qabuli uchun avtomatik transaction."""
    return await create_auto_transaction(
        db=db,
        transaction_type="expense",
        amount=amount,
        description=f"Xom-ashyo qabuli — {supplier_name}",
        reference_type="warehouse_receipt",
        reference_id=receipt_id,
        category_name="Xom-ashyo xarajatlari",
        Transaction=Transaction,
        TransactionCategory=TransactionCategory,
    )