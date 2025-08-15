from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Celery configuration specifically for Flower monitoring
celery_app = Celery(
    'autonama_data',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=[]  # No task imports - just for monitoring
)

# Basic configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Africa/Johannesburg',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Simple debug task for testing
@celery_app.task(bind=True)
def debug_task(self):
    return f'Request: {self.request!r}'

if __name__ == '__main__':
    celery_app.start() 