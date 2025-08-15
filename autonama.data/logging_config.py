import logging
import json
import sys
from datetime import datetime
from pathlib import Path

class CeleryJSONFormatter(logging.Formatter):
    """Custom JSON formatter for Celery structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "autonama_celery",
            "environment": "development",
            "host": "celery-container",
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add Celery-specific fields if present
        for attr in ['task_id', 'task_name', 'worker_name', 'queue', 'routing_key', 'eta', 'expires', 'retries', 'duration']:
            if hasattr(record, attr):
                log_entry[attr] = getattr(record, attr)
            
        return json.dumps(log_entry, ensure_ascii=False)


def setup_celery_logging():
    """Setup structured logging for Celery"""
    
    # Create logs directory (disabled due to permission issues)
    # log_dir = Path("/var/log/autonama")
    # log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # JSON formatter
    json_formatter = CeleryJSONFormatter()
    
    # Console handler (for Docker logs)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # File handler (disabled due to permission issues)
    # file_handler = logging.FileHandler("/var/log/autonama/celery.log")
    # file_handler.setFormatter(json_formatter)
    # file_handler.setLevel(logging.INFO)
    # root_logger.addHandler(file_handler)
    
    # Configure Celery loggers
    celery_loggers = [
        "celery",
        "celery.worker",
        "celery.beat",
        "celery.task",
        "celery.redirected",
        "autonama.tasks"
    ]
    
    for logger_name in celery_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = True
    
    return root_logger


def get_task_logger(name: str):
    """Get a task-specific logger"""
    return logging.getLogger(f"autonama.tasks.{name}")


# Task logging decorator
def log_task_execution(func):
    """Decorator to log task execution"""
    def wrapper(*args, **kwargs):
        task_logger = get_task_logger(func.__name__)
        task_id = getattr(func, 'request', {}).get('id', 'unknown')
        
        task_logger.info(
            f"Task {func.__name__} started",
            extra={
                "task_id": task_id,
                "task_name": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs)
            }
        )
        
        start_time = datetime.utcnow()
        try:
            result = func(*args, **kwargs)
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            task_logger.info(
                f"Task {func.__name__} completed successfully",
                extra={
                    "task_id": task_id,
                    "task_name": func.__name__,
                    "duration_ms": duration,
                    "status": "success"
                }
            )
            return result
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            task_logger.error(
                f"Task {func.__name__} failed: {str(e)}",
                extra={
                    "task_id": task_id,
                    "task_name": func.__name__,
                    "duration_ms": duration,
                    "status": "failed",
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise
    
    return wrapper
