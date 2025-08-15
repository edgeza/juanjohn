from celery import Celery
import os
from dotenv import load_dotenv
from logging_config import setup_celery_logging, get_task_logger

load_dotenv()

# Setup logging first
setup_celery_logging()
logger = get_task_logger("celery_app")

# Create runtime directory if it doesn't exist
runtime_dir = os.path.join(os.path.dirname(__file__), 'runtime', 'celery')
os.makedirs(runtime_dir, exist_ok=True)

# Celery configuration - MINIMAL: Only working tasks
celery_app = Celery(
    'autonama_data',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=[
        # Only include maintenance tasks for now
        'tasks.maintenance'
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Africa/Johannesburg',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Beat scheduler configuration - MINIMAL
    beat_schedule_filename=os.path.join(runtime_dir, 'celerybeat-schedule'),
    beat_schedule={
        # Only maintenance tasks for now
        'cleanup-old-data': {
            'task': 'tasks.maintenance.cleanup_old_data',
            'schedule': 86400.0,  # Daily
        },
        'health-check': {
            'task': 'tasks.maintenance.health_check',
            'schedule': 300.0,  # Every 5 minutes
        },
        'optimize-database': {
            'task': 'tasks.maintenance.optimize_database',
            'schedule': 604800.0,  # Weekly (7 days)
        },
    },
    # Logging configuration
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Task execution hooks for logging
@celery_app.task(bind=True)
def debug_task(self):
    logger.info(f'Request: {self.request!r}', extra={"task_id": self.request.id, "task_name": "debug_task"})

# Log Celery app startup
logger.info("Celery app initialized with minimal configuration", extra={
    "broker": celery_app.conf.broker_url, 
    "backend": celery_app.conf.result_backend,
    "focus": "minimal-configuration",
    "disabled": ["binance_asset_loader", "current_prices_updater"]
})

if __name__ == '__main__':
    celery_app.start() 