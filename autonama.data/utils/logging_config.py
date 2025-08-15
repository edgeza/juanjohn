import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
import redis
import os
from pythonjsonlogger import jsonlogger


class RedisLogHandler(logging.Handler):
    """Custom log handler that sends logs to Redis for ELK processing"""
    
    def __init__(self, redis_url: str, key: str = "autonama:logs"):
        super().__init__()
        self.redis_client = redis.from_url(redis_url)
        self.key = key
        
    def emit(self, record):
        try:
            log_entry = self.format(record)
            self.redis_client.lpush(self.key, log_entry)
            # Keep only last 10000 logs in Redis
            self.redis_client.ltrim(self.key, 0, 9999)
        except Exception:
            self.handleError(record)


class CeleryStructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for Celery structured logging"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['service'] = 'autonama_celery'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add process info
        log_record['process_id'] = record.process
        log_record['thread_id'] = record.thread
        
        # Add Celery-specific fields if present
        if hasattr(record, 'task_id'):
            log_record['task_id'] = record.task_id
        if hasattr(record, 'task_name'):
            log_record['task_name'] = record.task_name
        if hasattr(record, 'task_status'):
            log_record['task_status'] = record.task_status
        if hasattr(record, 'task_duration'):
            log_record['task_duration'] = record.task_duration
        if hasattr(record, 'worker_name'):
            log_record['worker_name'] = record.worker_name
        if hasattr(record, 'queue_name'):
            log_record['queue_name'] = record.queue_name


def setup_celery_logging():
    """Setup logging configuration for Celery workers"""
    
    # Get configuration from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    enable_elk = os.getenv('ENABLE_ELK_LOGGING', 'false').lower() == 'true'
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Create formatters
    json_formatter = CeleryStructuredFormatter(
        '%(timestamp)s %(level)s %(service)s %(logger)s %(message)s'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter if enable_elk else console_formatter)
    root_logger.addHandler(console_handler)
    
    # Redis handler for ELK stack
    if enable_elk:
        try:
            redis_handler = RedisLogHandler(redis_url)
            redis_handler.setFormatter(json_formatter)
            root_logger.addHandler(redis_handler)
        except Exception as e:
            logging.warning(f"Failed to setup Redis logging: {e}")
    
    # Configure specific loggers
    loggers_config = {
        'celery': logging.INFO,
        'celery.worker': logging.INFO,
        'celery.task': logging.INFO,
        'celery.beat': logging.INFO,
        'sqlalchemy.engine': logging.WARNING,
        'redis': logging.WARNING,
        'urllib3': logging.WARNING,
        'requests': logging.WARNING,
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)


# Task logging utilities
def log_task_start(logger: logging.Logger, task_name: str, task_id: str, 
                  args: tuple = None, kwargs: dict = None):
    """Log task start with structured data"""
    extra = {
        'task_name': task_name,
        'task_id': task_id,
        'task_status': 'STARTED',
        'log_type': 'task_lifecycle'
    }
    
    if args:
        extra['task_args'] = str(args)
    if kwargs:
        extra['task_kwargs'] = str(kwargs)
    
    logger.info(f"Task started: {task_name}[{task_id}]", extra=extra)


def log_task_success(logger: logging.Logger, task_name: str, task_id: str,
                    duration: float, result: Any = None):
    """Log task success with structured data"""
    extra = {
        'task_name': task_name,
        'task_id': task_id,
        'task_status': 'SUCCESS',
        'task_duration': duration,
        'log_type': 'task_lifecycle'
    }
    
    if result is not None:
        extra['task_result'] = str(result)[:1000]  # Limit result size
    
    logger.info(f"Task completed: {task_name}[{task_id}] in {duration:.3f}s", extra=extra)


def log_task_failure(logger: logging.Logger, task_name: str, task_id: str,
                    duration: float, error: Exception):
    """Log task failure with structured data"""
    extra = {
        'task_name': task_name,
        'task_id': task_id,
        'task_status': 'FAILURE',
        'task_duration': duration,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'log_type': 'task_lifecycle'
    }
    
    logger.error(f"Task failed: {task_name}[{task_id}] after {duration:.3f}s: {error}", 
                extra=extra, exc_info=True)


def log_task_retry(logger: logging.Logger, task_name: str, task_id: str,
                  retry_count: int, error: Exception):
    """Log task retry with structured data"""
    extra = {
        'task_name': task_name,
        'task_id': task_id,
        'task_status': 'RETRY',
        'retry_count': retry_count,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'log_type': 'task_lifecycle'
    }
    
    logger.warning(f"Task retry: {task_name}[{task_id}] attempt {retry_count}: {error}", 
                  extra=extra)


def log_optimization_metrics(logger: logging.Logger, strategy: str, symbol: str,
                           metrics: Dict[str, Any], task_id: str = None):
    """Log optimization metrics for analysis"""
    extra = {
        'strategy': strategy,
        'symbol': symbol,
        'metrics': metrics,
        'log_type': 'optimization_metrics'
    }
    
    if task_id:
        extra['task_id'] = task_id
    
    logger.info(f"Optimization metrics: {strategy} on {symbol}", extra=extra)


def log_market_data_update(logger: logging.Logger, symbol: str, timeframe: str,
                          records_count: int, task_id: str = None):
    """Log market data updates"""
    extra = {
        'symbol': symbol,
        'timeframe': timeframe,
        'records_count': records_count,
        'log_type': 'market_data_update'
    }
    
    if task_id:
        extra['task_id'] = task_id
    
    logger.info(f"Market data updated: {symbol} {timeframe} - {records_count} records", 
               extra=extra)
