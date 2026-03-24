"""add_production_goods_receipts

Revision ID: c9d4e5f6a7b8
Revises: b7d3e8f2c1a5
Create Date: 2026-03-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c9d4e5f6a7b8'
down_revision: Union[str, None] = 'b7d3e8f2c1a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect
    bind = op.get_bind()
    if 'production_goods_receipts' in inspect(bind).get_table_names():
        return
    op.create_table(
        'production_goods_receipts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('finished_product_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('finished_products.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('shift_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('shifts.id', ondelete='SET NULL'),
                  nullable=True, index=True),
        sa.Column('quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='approved'),
        sa.Column('received_at', sa.DateTime, nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table('production_goods_receipts')
