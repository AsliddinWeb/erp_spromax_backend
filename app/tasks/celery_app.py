from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Celery app
celery_app = Celery(
    "promax_erp",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Tashkent',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
)

# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    # Har soat: kam qoldiq tekshirish
    'check-low-stock-every-hour': {
        'task': 'app.tasks.warehouse_tasks.check_low_stock',
        'schedule': crontab(minute=0),
    },
    # Har kuni 23:50: kunlik sotuv xulosasi
    'daily-sales-summary': {
        'task': 'app.tasks.report_tasks.daily_sales_summary',
        'schedule': crontab(hour=23, minute=50),
    },
    # Har kuni 23:55: kunlik ishlab chiqarish xulosasi
    'daily-production-summary': {
        'task': 'app.tasks.report_tasks.daily_production_summary',
        'schedule': crontab(hour=23, minute=55),
    },
    # Har dushanba 02:00: eski audit loglarni tozalash
    'clear-old-audit-logs-weekly': {
        'task': 'app.tasks.report_tasks.clear_old_audit_logs',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])