"""
Celery worker for processing background tasks from the queue.
"""
import os
import logging
from celery import Celery
from shared.queue import TaskQueue
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
app = Celery(
    'data_worker',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/1'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/2')
)

# Initialize task queue
queue = TaskQueue()

# Import task handlers after Celery app is created to avoid circular imports
from task_handlers import get_task_handler

@app.task(bind=True, max_retries=3)
def process_task(self, task_data: dict):
    """
    Process a task from the queue.
    
    Args:
        task_data: Task data from the queue
    """
    task_id = task_data.get('id')
    task_type = task_data.get('type')
    payload = task_data.get('payload', {})
    
    logger.info(f"Processing task {task_id} of type {task_type}")
    
    try:
        # Get the appropriate handler for this task type
        try:
            handler = get_task_handler(task_type)
        except ValueError as e:
            error_msg = str(e)
            logger.error(error_msg)
            queue.update_task(task_id, status='failed', error=error_msg)
            return
        
        # Update task status to processing
        queue.update_task(task_id, status='processing', started_at=datetime.utcnow().isoformat())
        
        # Process the task
        result = handler(payload)
        
        # Update task status to completed
        queue.update_task(
            task_id,
            status='completed',
            completed_at=datetime.utcnow().isoformat(),
            result=result
        )
        
        logger.info(f"Successfully processed task {task_id}")
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing task {task_id}: {error_msg}", exc_info=True)
        queue.update_task(
            task_id,
            status='failed',
            error=error_msg,
            completed_at=datetime.utcnow().isoformat()
        )
        # Retry the task if needed
        raise self.retry(exc=e, countdown=60)

def start_worker():
    """Start the Celery worker."""
    logger.info("Starting data worker...")
    app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=4',
        '--without-gossip',
        '--without-mingle',
        '--without-heartbeat'
    ])

if __name__ == '__main__':
    start_worker()
