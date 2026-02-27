from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

import sys
from os.path import dirname, abspath
sys.path.append(dirname(dirname(abspath(__file__))))

from app.config import settings
from app.database import Base

# BARCHA MODELLARNI IMPORT QILING
from app.models.user import User, Role, Permission
from app.models.warehouse import (
    Supplier,
    RawMaterial,
    WarehouseReceipt,
    WarehouseStock,
    MaterialRequest
)
from app.models.production import (
    ProductionLine,
    Machine,
    FinishedProduct,
    Shift,
    ShiftMachine,
    ProductionRecord,
    ProductionOutput,
    DefectReason,
    DefectiveProduct,
    ShiftHandover,
    FinishedProductStock,
    # Yangilar:
    ShiftPause,
    ScrapStock,
    ScrapStockTransaction,
    ShiftScrapUsage,
)
from app.models.sales import (
    Customer,
    Order,
    OrderItem,
    Payment
)
from app.models.finance import (
    TransactionCategory,
    FinancialTransaction
)
from app.models.hr import (
    Department,
    Employee,
    Attendance,
    SalaryPayment,
    LeaveRequest
)
from app.models.maintenance import (
    MaintenanceRequest,
    MaintenanceLog,
    SparePart,
    SparePartUsage,
    MaintenanceSchedule
)

from app.models.notification import Notification

# this is the Alembic Config object
config = context.config

# DATABASE_URL ni .env dan olish
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()