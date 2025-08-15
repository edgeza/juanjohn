"""
Error Handler Utility

Centralized error handling for data processors and tasks.
Provides consistent error handling, logging, and recovery strategies.
"""

import logging
import traceback
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories"""
    NETWORK = "network"
    API_LIMIT = "api_limit"
    DATA_VALIDATION = "data_validation"
    DATABASE = "database"
    PROCESSOR = "processor"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"

class ProcessorError(Exception):
    """Base exception for processor errors"""
    
    def __init__(
        self, 
        message: str, 
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        processor: Optional[str] = None,
        symbol: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.processor = processor
        self.symbol = symbol
        self.details = details or {}
        self.timestamp = datetime.now()

class NetworkError(ProcessorError):
    """Network-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.NETWORK, **kwargs)

class APILimitError(ProcessorError):
    """API rate limit errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.API_LIMIT, **kwargs)

class DataValidationError(ProcessorError):
    """Data validation errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.DATA_VALIDATION, **kwargs)

class DatabaseError(ProcessorError):
    """Database-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.DATABASE, **kwargs)

class ConfigurationError(ProcessorError):
    """Configuration-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.CONFIGURATION, severity=ErrorSeverity.HIGH, **kwargs)

class ErrorHandler:
    """Centralized error handler"""
    
    def __init__(self, logger_name: str = "error_handler"):
        self.logger = logging.getLogger(logger_name)
        self.error_counts: Dict[str, int] = {}
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        
    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable):
        """Register a recovery strategy for an error category"""
        self.recovery_strategies[category] = strategy
        
    def handle_error(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an error with appropriate logging and recovery
        
        Args:
            error: The exception that occurred
            context: Additional context information
            
        Returns:
            Dict with error information and recovery actions
        """
        context = context or {}
        
        # Convert to ProcessorError if needed
        if not isinstance(error, ProcessorError):
            processor_error = ProcessorError(
                message=str(error),
                category=self._categorize_error(error),
                severity=self._assess_severity(error),
                processor=context.get('processor'),
                symbol=context.get('symbol'),
                details=context
            )
        else:
            processor_error = error
            
        # Log the error
        self._log_error(processor_error, context)
        
        # Update error counts
        error_key = f"{processor_error.category.value}_{processor_error.processor or 'unknown'}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Attempt recovery
        recovery_result = self._attempt_recovery(processor_error)
        
        return {
            'error': {
                'message': processor_error.message,
                'category': processor_error.category.value,
                'severity': processor_error.severity.value,
                'processor': processor_error.processor,
                'symbol': processor_error.symbol,
                'timestamp': processor_error.timestamp.isoformat(),
                'details': processor_error.details
            },
            'recovery': recovery_result,
            'error_count': self.error_counts.get(error_key, 0)
        }
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize an error based on its type and message"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Network errors
        if any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'unreachable']):
            return ErrorCategory.NETWORK
        if any(keyword in error_type for keyword in ['connection', 'timeout', 'network']):
            return ErrorCategory.NETWORK
            
        # API limit errors
        if any(keyword in error_str for keyword in ['rate limit', 'too many requests', '429', 'quota']):
            return ErrorCategory.API_LIMIT
            
        # Data validation errors
        if any(keyword in error_str for keyword in ['validation', 'invalid', 'format', 'parse']):
            return ErrorCategory.DATA_VALIDATION
        if any(keyword in error_type for keyword in ['validation', 'value', 'type']):
            return ErrorCategory.DATA_VALIDATION
            
        # Database errors
        if any(keyword in error_str for keyword in ['database', 'sql', 'connection', 'query']):
            return ErrorCategory.DATABASE
        if any(keyword in error_type for keyword in ['database', 'sql', 'operational']):
            return ErrorCategory.DATABASE
            
        # Configuration errors
        if any(keyword in error_str for keyword in ['config', 'setting', 'environment', 'missing']):
            return ErrorCategory.CONFIGURATION
            
        return ErrorCategory.UNKNOWN
    
    def _assess_severity(self, error: Exception) -> ErrorSeverity:
        """Assess the severity of an error"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Critical errors
        if any(keyword in error_str for keyword in ['critical', 'fatal', 'system']):
            return ErrorSeverity.CRITICAL
        if any(keyword in error_type for keyword in ['system', 'critical']):
            return ErrorSeverity.CRITICAL
            
        # High severity errors
        if any(keyword in error_str for keyword in ['database', 'config', 'auth']):
            return ErrorSeverity.HIGH
            
        # Low severity errors
        if any(keyword in error_str for keyword in ['rate limit', 'temporary', 'retry']):
            return ErrorSeverity.LOW
            
        return ErrorSeverity.MEDIUM
    
    def _log_error(self, error: ProcessorError, context: Dict[str, Any]):
        """Log an error with appropriate level and context"""
        log_data = {
            'error_category': error.category.value,
            'error_severity': error.severity.value,
            'processor': error.processor,
            'symbol': error.symbol,
            'timestamp': error.timestamp.isoformat(),
            'traceback': traceback.format_exc(),
            **context
        }
        
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(error.message, extra=log_data)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(error.message, extra=log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(error.message, extra=log_data)
        else:
            self.logger.info(error.message, extra=log_data)
    
    def _attempt_recovery(self, error: ProcessorError) -> Dict[str, Any]:
        """Attempt to recover from an error"""
        recovery_result = {
            'attempted': False,
            'successful': False,
            'action': None,
            'message': None
        }
        
        # Check if we have a recovery strategy for this error category
        if error.category in self.recovery_strategies:
            try:
                recovery_result['attempted'] = True
                strategy = self.recovery_strategies[error.category]
                result = strategy(error)
                
                recovery_result['successful'] = True
                recovery_result['action'] = result.get('action', 'unknown')
                recovery_result['message'] = result.get('message', 'Recovery successful')
                
            except Exception as recovery_error:
                recovery_result['successful'] = False
                recovery_result['message'] = f"Recovery failed: {str(recovery_error)}"
                self.logger.error(f"Recovery strategy failed: {recovery_error}")
        
        return recovery_result
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        total_errors = sum(self.error_counts.values())
        
        return {
            'total_errors': total_errors,
            'error_counts': self.error_counts.copy(),
            'top_errors': sorted(
                self.error_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
        }
    
    def reset_error_counts(self):
        """Reset error counts"""
        self.error_counts.clear()

# Global error handler instance
global_error_handler = ErrorHandler()

def handle_processor_error(
    error: Exception, 
    processor: str, 
    symbol: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to handle processor errors
    
    Args:
        error: The exception that occurred
        processor: Name of the processor
        symbol: Asset symbol (if applicable)
        context: Additional context
        
    Returns:
        Dict with error information
    """
    context = context or {}
    context.update({
        'processor': processor,
        'symbol': symbol
    })
    
    return global_error_handler.handle_error(error, context)

# Default recovery strategies
def network_recovery_strategy(error: ProcessorError) -> Dict[str, Any]:
    """Recovery strategy for network errors"""
    return {
        'action': 'retry_with_backoff',
        'message': 'Will retry with exponential backoff'
    }

def api_limit_recovery_strategy(error: ProcessorError) -> Dict[str, Any]:
    """Recovery strategy for API limit errors"""
    return {
        'action': 'wait_and_retry',
        'message': 'Will wait for rate limit reset and retry'
    }

def data_validation_recovery_strategy(error: ProcessorError) -> Dict[str, Any]:
    """Recovery strategy for data validation errors"""
    return {
        'action': 'skip_and_log',
        'message': 'Will skip invalid data and continue processing'
    }

# Convenience functions for backward compatibility
def handle_processor_errors(processor_name=None, function_name=None):
    """Decorator for handling processor errors"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                proc_name = processor_name or func.__module__
                func_name = function_name or func.__name__
                handle_processor_error(e, proc_name, symbol=None, context={'function': func_name})
                raise
        return wrapper
    
    # Handle both @handle_processor_errors and @handle_processor_errors('name', 'func')
    if callable(processor_name):
        # Called as @handle_processor_errors (without parentheses)
        func = processor_name
        processor_name = None
        return decorator(func)
    else:
        # Called as @handle_processor_errors('name', 'func')
        return decorator

def retry_on_error(max_retries=3, delay=1):
    """Decorator for retrying on errors"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator

def create_error_context(processor: str, function: str, **kwargs) -> Dict[str, Any]:
    """Create error context dictionary"""
    return {
        'processor': processor,
        'function': function,
        'timestamp': datetime.now().isoformat(),
        **kwargs
    }

def get_error_handler():
    """Get the global error handler instance"""
    return global_error_handler

# Alias for backward compatibility
APIError = NetworkError
RateLimitError = APILimitError
ValidationError = DataValidationError

# Register default recovery strategies
global_error_handler.register_recovery_strategy(ErrorCategory.NETWORK, network_recovery_strategy)
global_error_handler.register_recovery_strategy(ErrorCategory.API_LIMIT, api_limit_recovery_strategy)
global_error_handler.register_recovery_strategy(ErrorCategory.DATA_VALIDATION, data_validation_recovery_strategy)
