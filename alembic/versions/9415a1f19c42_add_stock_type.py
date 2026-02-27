"""add stock_type

Revision ID: 9415a1f19c42
Revises: 830b19ad2aec
Create Date: 2026-02-27 15:50:27.070621

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9415a1f19c42'
down_revision: Union[str, None] = '830b19ad2aec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # scrap_stock
    op.add_column('scrap_stock', sa.Column('stock_type', sa.String(length=20), nullable=True))
    op.execute("UPDATE scrap_stock SET stock_type = 'brak' WHERE stock_type IS NULL")
    op.alter_column('scrap_stock', 'stock_type', nullable=False)
    op.drop_constraint('scrap_stock_finished_product_id_key', 'scrap_stock', type_='unique')
    op.create_unique_constraint('uq_scrap_product_type', 'scrap_stock', ['finished_product_id', 'stock_type'])

    # scrap_stock_transactions
    op.add_column('scrap_stock_transactions', sa.Column('stock_type', sa.String(length=20), nullable=True))
    op.execute("UPDATE scrap_stock_transactions SET stock_type = 'brak' WHERE stock_type IS NULL")
    op.alter_column('scrap_stock_transactions', 'stock_type', nullable=False)


def downgrade() -> None:
    op.drop_column('scrap_stock_transactions', 'stock_type')
    op.drop_constraint('uq_scrap_product_type', 'scrap_stock', type_='unique')
    op.create_unique_constraint('scrap_stock_finished_product_id_key', 'scrap_stock', ['finished_product_id'])
    op.drop_column('scrap_stock', 'stock_type')