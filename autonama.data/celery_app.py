from celery import Celery
import os
from dotenv import load_dotenv
from logging_config import setup_celery_logging, get_task_logger

load_dotenv()

# Setup logging first
setup_celery_logging()
logger = get_task_logger("celery_app")

# Create runtime directory if it doesn't exist
runtime_dir = os.getenv('CELERY_RUNTIME_DIR', '/tmp/celery')
try:
    os.makedirs(runtime_dir, exist_ok=True)
except Exception:
    # Fallback to /tmp if runtime_dir not writable
    runtime_dir = '/tmp/celery'
    os.makedirs(runtime_dir, exist_ok=True)

# Celery configuration - SIMPLIFIED: Focus on crypto only
celery_app = Celery(
    'autonama_data',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=[
        'tasks.binance_asset_loader',      # Top 100 crypto assets
        'tasks.current_prices_updater',    # Live price updates
        'tasks.maintenance'                # System maintenance
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
    # Beat scheduler configuration - SIMPLIFIED
    beat_schedule_filename=os.path.join(runtime_dir, 'celerybeat-schedule'),
    beat_schedule={
        # CRYPTO-ONLY TASKS
        
        # Load top 100 Binance assets (every 6 hours)
        'load-top-100-binance-assets': {
            'task': 'tasks.binance_asset_loader.load_top_100_binance_assets',
            'schedule': 21600.0,  # Every 6 hours (6 * 60 * 60 = 21600 seconds)
        },
        
        # Refresh top 100 assets daily
        'refresh-top-100-assets': {
            'task': 'tasks.binance_asset_loader.refresh_top_100_assets',
            'schedule': 86400.0,  # Daily (24 hours)
        },
        
        # Update current prices every 5 minutes
        'update-current-prices': {
            'task': 'tasks.current_prices_updater.update_current_prices',
            'schedule': 300.0,  # Every 5 minutes (5 * 60 = 300 seconds)
        },
        
        # Maintenance tasks
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
logger.info("Celery app initialized with crypto-only focus", extra={
    "broker": celery_app.conf.broker_url, 
    "backend": celery_app.conf.result_backend,
    "focus": "crypto-only",
    "removed": ["optimization", "multi-asset", "analytics", "backtest_ingestion"]
})

if __name__ == '__main__':
    celery_app.start()
