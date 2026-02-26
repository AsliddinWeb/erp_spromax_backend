"""add_is_paid_to_leave_requests

Revision ID: 632a4a19600c
Revises: 13384101e3db
Create Date: 2026-02-26 12:39:03.990465

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '632a4a19600c'
down_revision: Union[str, None] = '13384101e3db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('leave_requests',
        sa.Column('is_paid', sa.Boolean(), nullable=True, server_default='false')
    )
    op.execute("UPDATE leave_requests SET is_paid = false WHERE is_paid IS NULL")
    op.alter_column('leave_requests', 'is_paid', nullable=False, server_default=None)


def downgrade() -> None:
    op.drop_column('leave_requests', 'is_paid')