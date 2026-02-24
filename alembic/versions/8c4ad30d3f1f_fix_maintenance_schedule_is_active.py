"""fix_maintenance_schedule_is_active

Revision ID: 8c4ad30d3f1f
Revises: 05ccb614c648
Create Date: 2026-02-24 11:01:19.647584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c4ad30d3f1f'
down_revision: Union[str, None] = '05ccb614c648'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # BUG FIX: USING qo'shildi — 'active' → true, boshqa → false
    op.execute("""
        ALTER TABLE maintenance_schedules 
        ALTER COLUMN is_active TYPE boolean 
        USING CASE WHEN is_active = 'active' THEN true ELSE false END
    """)


def downgrade() -> None:
    # Qaytarish: boolean → varchar
    op.execute("""
        ALTER TABLE maintenance_schedules 
        ALTER COLUMN is_active TYPE varchar(20) 
        USING CASE WHEN is_active = true THEN 'active' ELSE 'inactive' END
    """)