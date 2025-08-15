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


class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['service'] = 'autonama_api'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add process info
        log_record['process_id'] = record.process
        log_record['thread_id'] = record.thread
        
        # Add custom fields if present
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'endpoint'):
            log_record['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_record['method'] = record.method
        if hasattr(record, 'status_code'):
            log_record['status_code'] = record.status_code
        if hasattr(record, 'response_time'):
            log_record['response_time'] = record.response_time
        if hasattr(record, 'error_type'):
            log_record['error_type'] = record.error_type


def setup_logging():
    """Setup logging configuration for the application"""
    
    # Get configuration from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    enable_elk = os.getenv('ENABLE_ELK_LOGGING', 'false').lower() == 'true'
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Create formatters
    json_formatter = StructuredFormatter(
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
        'uvicorn': logging.INFO,
        'uvicorn.access': logging.INFO,
        'fastapi': logging.INFO,
        'sqlalchemy.engine': logging.WARNING,  # Reduce SQL query noise
        'celery': logging.INFO,
        'redis': logging.WARNING,
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)


# Request logging utilities
def log_request(logger: logging.Logger, method: str, endpoint: str, 
                status_code: int, response_time: float, user_id: str = None,
                request_id: str = None):
    """Log HTTP request with structured data"""
    extra = {
        'method': method,
        'endpoint': endpoint,
        'status_code': status_code,
        'response_time': response_time,
        'log_type': 'http_request'
    }
    
    if user_id:
        extra['user_id'] = user_id
    if request_id:
        extra['request_id'] = request_id
    
    level = logging.ERROR if status_code >= 400 else logging.INFO
    logger.log(level, f"{method} {endpoint} - {status_code} - {response_time:.3f}s", extra=extra)


def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """Log error with structured data"""
    extra = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'log_type': 'error'
    }
    
    if context:
        extra.update(context)
    
    logger.error(f"Error occurred: {error}", extra=extra, exc_info=True)


def log_business_event(logger: logging.Logger, event_type: str, 
                      event_data: Dict[str, Any], user_id: str = None):
    """Log business events for analytics"""
    extra = {
        'event_type': event_type,
        'event_data': event_data,
        'log_type': 'business_event'
    }
    
    if user_id:
        extra['user_id'] = user_id
    
    logger.info(f"Business event: {event_type}", extra=extra)


def log_performance(logger: logging.Logger, operation: str, duration: float,
                   metadata: Dict[str, Any] = None):
    """Log performance metrics"""
    extra = {
        'operation': operation,
        'duration': duration,
        'log_type': 'performance'
    }
    
    if metadata:
        extra.update(metadata)
    
    level = logging.WARNING if duration > 1.0 else logging.INFO
    logger.log(level, f"Performance: {operation} took {duration:.3f}s", extra=extra)
