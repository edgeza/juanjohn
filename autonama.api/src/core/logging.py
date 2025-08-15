import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pathlib import Path
import os

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "autonama_api",
            "environment": "development",
            "host": "api-container",
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
            
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging():
    """Setup structured logging for the application"""
    
    # Create logs directory in app directory (writable by container user)
    log_dir = Path("/app/logs")
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # If we can't create the directory, just use console logging
        pass
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # JSON formatter
    json_formatter = JSONFormatter()
    
    # Console handler (for Docker logs)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # File handler (only if we can write to the logs directory)
    try:
        if log_dir.exists() and os.access(log_dir, os.W_OK):
            file_handler = logging.FileHandler("/app/logs/api.log")
            file_handler.setFormatter(json_formatter)
            file_handler.setLevel(logging.INFO)
            root_logger.addHandler(file_handler)
    except (PermissionError, OSError):
        # If we can't write to the file, just use console logging
        pass
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)
