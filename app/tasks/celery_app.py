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
    'check-low-stock-every-hour': {
        'task': 'app.tasks.warehouse_tasks.check_low_stock',
        'schedule': crontab(minute=0),  # Har soat
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])