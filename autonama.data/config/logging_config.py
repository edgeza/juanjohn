"""
Centralized Logging Configuration

This module provides centralized logging configuration for all data processors
with structured logging, multiple handlers, and ELK stack integration.
"""

import os
import sys
import logging
import logging.config
from datetime import datetime
from typing import Dict, Any, Optional
import json
from pathlib import Path

# Default logging configuration
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_DIR = "/var/log/autonama"


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging with JSON output.
    Compatible with ELK stack and other log aggregation systems.
    """
    
    def __init__(self, service_name: str = "autonama_data", environment: str = "development"):
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.hostname = os.uname().nodename if hasattr(os, 'uname') else 'unknown'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log structure
        log_entry = {
            "@timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
            "host": self.hostname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields') and record.extra_fields:
            log_entry.update(record.extra_fields)
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add stack trace for warnings and errors
        if record.levelno >= logging.WARNING and record.stack_info:
            log_entry["stack_trace"] = record.stack_info
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class ProcessorLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter for processors to add processor-specific context.
    """
    
    def __init__(self, logger: logging.Logger, processor_name: str, extra: Optional[Dict[str, Any]] = None):
        self.processor_name = processor_name
        super().__init__(logger, extra or {})
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add processor context to log messages."""
        # Add processor name to extra fields
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        if 'extra_fields' not in kwargs['extra']:
            kwargs['extra']['extra_fields'] = {}
        
        kwargs['extra']['extra_fields']['processor'] = self.processor_name
        
        # Add any additional context from the adapter
        if self.extra:
            kwargs['extra']['extra_fields'].update(self.extra)
        
        return msg, kwargs


def setup_logging(
    service_name: str = "autonama_data",
    environment: str = None,
    log_level: str = None,
    log_dir: str = None,
    enable_elk: bool = None,
    enable_console: bool = True,
    enable_file: bool = True
) -> None:
    """
    Set up centralized logging configuration.
    
    Args:
        service_name: Name of the service for logging context
        environment: Environment (development, staging, production)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        enable_elk: Enable ELK stack compatible logging
        enable_console: Enable console logging
        enable_file: Enable file logging
    """
    # Get configuration from environment variables
    environment = environment or os.getenv('ENVIRONMENT', 'development')
    log_level = log_level or os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL)
    log_dir = log_dir or os.getenv('LOG_DIR', DEFAULT_LOG_DIR)
    enable_elk = enable_elk if enable_elk is not None else os.getenv('ENABLE_ELK_LOGGING', 'false').lower() == 'true'
    
    # Ensure log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': DEFAULT_LOG_FORMAT,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'structured': {
                '()': StructuredFormatter,
                'service_name': service_name,
                'environment': environment
            }
        },
        'handlers': {},
        'loggers': {
            '': {  # Root logger
                'level': log_level,
                'handlers': []
            },
            'autonama': {
                'level': log_level,
                'handlers': [],
                'propagate': False
            },
            'celery': {
                'level': 'INFO',
                'handlers': [],
                'propagate': False
            },
            'sqlalchemy': {
                'level': 'WARNING',
                'handlers': [],
                'propagate': False
            }
        }
    }
    
    # Console handler
    if enable_console:
        console_formatter = 'structured' if enable_elk else 'standard'
        logging_config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': console_formatter,
            'stream': sys.stdout
        }
        
        # Add console handler to all loggers
        for logger_name in logging_config['loggers']:
            logging_config['loggers'][logger_name]['handlers'].append('console')
    
    # File handlers
    if enable_file:
        # General application log
        logging_config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'structured' if enable_elk else 'detailed',
            'filename': os.path.join(log_dir, f'{service_name}.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }
        
        # Error log
        logging_config['handlers']['error_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'structured' if enable_elk else 'detailed',
            'filename': os.path.join(log_dir, f'{service_name}_errors.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }
        
        # Processor-specific log
        logging_config['handlers']['processor_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'structured' if enable_elk else 'detailed',
            'filename': os.path.join(log_dir, f'{service_name}_processors.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 10,
            'encoding': 'utf-8'
        }
        
        # Add file handlers to loggers
        for logger_name in logging_config['loggers']:
            logging_config['loggers'][logger_name]['handlers'].extend(['file', 'error_file'])
        
        # Add processor file handler to autonama logger
        logging_config['loggers']['autonama']['handlers'].append('processor_file')
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Log configuration success
    logger = logging.getLogger('autonama.logging')
    logger.info(
        f"Logging configured successfully",
        extra={
            'extra_fields': {
                'service': service_name,
                'environment': environment,
                'log_level': log_level,
                'log_dir': log_dir,
                'elk_enabled': enable_elk,
                'console_enabled': enable_console,
                'file_enabled': enable_file
            }
        }
    )


def get_logger(name: str, processor_name: str = None) -> logging.Logger:
    """
    Get a logger instance with optional processor context.
    
    Args:
        name: Logger name
        processor_name: Optional processor name for context
        
    Returns:
        Logger instance or ProcessorLoggerAdapter
    """
    logger = logging.getLogger(name)
    
    if processor_name:
        return ProcessorLoggerAdapter(logger, processor_name)
    
    return logger


def get_processor_logger(processor_name: str, extra_context: Optional[Dict[str, Any]] = None) -> ProcessorLoggerAdapter:
    """
    Get a processor-specific logger with context.
    
    Args:
        processor_name: Name of the processor
        extra_context: Additional context to include in logs
        
    Returns:
        ProcessorLoggerAdapter instance
    """
    logger = logging.getLogger(f'autonama.processors.{processor_name}')
    return ProcessorLoggerAdapter(logger, processor_name, extra_context)


def log_processor_metrics(processor_name: str, metrics: Dict[str, Any]) -> None:
    """
    Log processor performance metrics.
    
    Args:
        processor_name: Name of the processor
        metrics: Dictionary of metrics to log
    """
    logger = get_processor_logger(processor_name)
    logger.info(
        f"Processor metrics for {processor_name}",
        extra={
            'extra_fields': {
                'event_type': 'processor_metrics',
                'processor': processor_name,
                **metrics
            }
        }
    )


def log_api_request(processor_name: str, api_name: str, endpoint: str, 
                   status_code: int, response_time: float, error: str = None) -> None:
    """
    Log API request details.
    
    Args:
        processor_name: Name of the processor making the request
        api_name: Name of the API (e.g., 'binance', 'twelvedata')
        endpoint: API endpoint called
        status_code: HTTP status code
        response_time: Response time in seconds
        error: Error message if request failed
    """
    logger = get_processor_logger(processor_name)
    
    log_level = logging.INFO if status_code < 400 else logging.ERROR
    message = f"API request to {api_name} {endpoint}"
    
    extra_fields = {
        'event_type': 'api_request',
        'processor': processor_name,
        'api_name': api_name,
        'endpoint': endpoint,
        'status_code': status_code,
        'response_time_seconds': response_time,
        'success': status_code < 400
    }
    
    if error:
        extra_fields['error'] = error
        message += f" failed: {error}"
    else:
        message += f" succeeded in {response_time:.3f}s"
    
    logger.log(log_level, message, extra={'extra_fields': extra_fields})


def log_data_ingestion(processor_name: str, symbol: str, records_count: int, 
                      timeframe: str = None, source: str = None) -> None:
    """
    Log data ingestion events.
    
    Args:
        processor_name: Name of the processor
        symbol: Asset symbol
        records_count: Number of records ingested
        timeframe: Data timeframe
        source: Data source
    """
    logger = get_processor_logger(processor_name)
    
    message = f"Ingested {records_count} records for {symbol}"
    if timeframe:
        message += f" ({timeframe})"
    
    extra_fields = {
        'event_type': 'data_ingestion',
        'processor': processor_name,
        'symbol': symbol,
        'records_count': records_count
    }
    
    if timeframe:
        extra_fields['timeframe'] = timeframe
    if source:
        extra_fields['source'] = source
    
    logger.info(message, extra={'extra_fields': extra_fields})


# Initialize logging when module is imported
if not logging.getLogger().handlers:
    setup_logging()


# Export commonly used functions
__all__ = [
    'setup_logging',
    'get_logger',
    'get_processor_logger',
    'log_processor_metrics',
    'log_api_request',
    'log_data_ingestion',
    'ProcessorLoggerAdapter',
    'StructuredFormatter'
]
