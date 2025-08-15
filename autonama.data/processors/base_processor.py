"""
Base Processor Class

This module provides the base class for all data processors with common functionality
including logging, error handling, rate limiting, and database connections.
"""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import threading
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProcessorStatus(Enum):
    """Processor status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class ProcessorMetrics:
    """Processor performance metrics."""
    requests_made: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    last_request_time: Optional[datetime] = None
    last_error: Optional[str] = None
    total_runtime: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.requests_made == 0:
            return 0.0
        return (self.requests_successful / self.requests_made) * 100
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage."""
        if self.requests_made == 0:
            return 0.0
        return (self.requests_failed / self.requests_made) * 100


class BaseProcessor(ABC):
    """
    Base class for all data processors.
    
    Provides common functionality:
    - Logging and error handling
    - Rate limiting
    - Metrics collection
    - Database connection management
    - Configuration management
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        Initialize the base processor.
        
        Args:
            name: Processor name for logging and identification
            config: Configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.status = ProcessorStatus.IDLE
        self.metrics = ProcessorMetrics()
        self._lock = threading.Lock()
        
        # Set up logging
        self.logger = logging.getLogger(f"autonama.processors.{name}")
        self.logger.info(f"Initialized {name} processor")
        
        # Initialize rate limiting
        self._rate_limit_requests = self.config.get('rate_limit_requests', 60)
        self._rate_limit_period = self.config.get('rate_limit_period', 60)  # seconds
        self._request_timestamps = []
        
        # Initialize retry configuration
        self._max_retries = self.config.get('max_retries', 3)
        self._retry_delay = self.config.get('retry_delay', 1.0)
        self._backoff_multiplier = self.config.get('backoff_multiplier', 2.0)
    
    @abstractmethod
    def process_data(self, *args, **kwargs) -> Any:
        """
        Abstract method for processing data.
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Abstract method for validating processor configuration.
        Must be implemented by subclasses.
        """
        pass
    
    def start(self) -> bool:
        """
        Start the processor.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            with self._lock:
                if self.status == ProcessorStatus.RUNNING:
                    self.logger.warning(f"{self.name} processor is already running")
                    return True
                
                if not self.validate_config():
                    self.logger.error(f"{self.name} processor configuration is invalid")
                    self.status = ProcessorStatus.ERROR
                    return False
                
                self.status = ProcessorStatus.RUNNING
                self.logger.info(f"{self.name} processor started successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to start {self.name} processor: {e}")
            self.status = ProcessorStatus.ERROR
            return False
    
    def stop(self) -> bool:
        """
        Stop the processor.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            with self._lock:
                self.status = ProcessorStatus.STOPPED
                self.logger.info(f"{self.name} processor stopped")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to stop {self.name} processor: {e}")
            return False
    
    def wait_for_rate_limit(self) -> None:
        """
        Wait if necessary to respect rate limits.
        """
        with self._lock:
            now = datetime.now()
            
            # Remove old timestamps outside the rate limit period
            cutoff_time = now - timedelta(seconds=self._rate_limit_period)
            self._request_timestamps = [
                ts for ts in self._request_timestamps if ts > cutoff_time
            ]
            
            # Check if we need to wait
            if len(self._request_timestamps) >= self._rate_limit_requests:
                # Calculate wait time
                oldest_request = min(self._request_timestamps)
                wait_time = self._rate_limit_period - (now - oldest_request).total_seconds()
                
                if wait_time > 0:
                    self.logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                    time.sleep(wait_time)
            
            # Record this request
            self._request_timestamps.append(now)
    
    def execute_with_retry(self, func, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic and exponential backoff.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None
        delay = self._retry_delay
        
        for attempt in range(self._max_retries + 1):
            try:
                # Wait for rate limit before each attempt
                self.wait_for_rate_limit()
                
                # Record request attempt
                self.metrics.requests_made += 1
                self.metrics.last_request_time = datetime.now()
                
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                # Record successful request
                self.metrics.requests_successful += 1
                self.metrics.total_runtime += (end_time - start_time)
                
                return result
                
            except Exception as e:
                last_exception = e
                self.metrics.requests_failed += 1
                self.metrics.last_error = str(e)
                
                if attempt < self._max_retries:
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed for {self.name}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)
                    delay *= self._backoff_multiplier
                else:
                    self.logger.error(
                        f"All {self._max_retries + 1} attempts failed for {self.name}: {e}"
                    )
        
        # If we get here, all retries were exhausted
        raise last_exception
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get processor status and metrics.
        
        Returns:
            Dict containing status and metrics
        """
        return {
            'name': self.name,
            'status': self.status.value,
            'metrics': {
                'requests_made': self.metrics.requests_made,
                'requests_successful': self.metrics.requests_successful,
                'requests_failed': self.metrics.requests_failed,
                'success_rate': self.metrics.success_rate,
                'error_rate': self.metrics.error_rate,
                'last_request_time': self.metrics.last_request_time.isoformat() if self.metrics.last_request_time else None,
                'last_error': self.metrics.last_error,
                'total_runtime': self.metrics.total_runtime
            },
            'config': {
                'rate_limit_requests': self._rate_limit_requests,
                'rate_limit_period': self._rate_limit_period,
                'max_retries': self._max_retries,
                'retry_delay': self._retry_delay
            }
        }
    
    def reset_metrics(self) -> None:
        """Reset processor metrics."""
        with self._lock:
            self.metrics = ProcessorMetrics()
            self.logger.info(f"Reset metrics for {self.name} processor")
    
    def __str__(self) -> str:
        """String representation of the processor."""
        return f"{self.__class__.__name__}(name='{self.name}', status='{self.status.value}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the processor."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"status='{self.status.value}', "
            f"requests_made={self.metrics.requests_made}, "
            f"success_rate={self.metrics.success_rate:.1f}%"
            f")"
        )
