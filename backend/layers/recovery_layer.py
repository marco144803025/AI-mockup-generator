"""
Recovery Layer - Error handling, retry logic, backoff strategies
"""

import time
import logging
import asyncio
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from functools import wraps
from enum import Enum

T = TypeVar('T')

class RetryStrategy(Enum):
    """Retry strategies for different types of failures"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"

class RecoveryLayer:
    """Handles error recovery, retries, and backoff strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
        
    def retry_with_backoff(
        self, 
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        exceptions: tuple = (Exception,)
    ):
        """Decorator for retry logic with exponential backoff"""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt == max_retries:
                            self.logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}")
                            raise e
                        
                        delay = self._calculate_delay(attempt, base_delay, max_delay, strategy)
                        self.logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                
                raise last_exception
            return wrapper
        return decorator
    
    def _calculate_delay(self, attempt: int, base_delay: float, max_delay: float, strategy: RetryStrategy) -> float:
        """Calculate delay based on retry strategy"""
        if strategy == RetryStrategy.LINEAR:
            delay = base_delay * (attempt + 1)
        elif strategy == RetryStrategy.EXPONENTIAL:
            delay = base_delay * (2 ** attempt)
        elif strategy == RetryStrategy.FIBONACCI:
            delay = base_delay * self._fibonacci(attempt + 1)
        else:
            delay = base_delay
            
        return min(delay, max_delay)
    
    def _fibonacci(self, n: int) -> int:
        """Calculate fibonacci number"""
        if n <= 1:
            return n
        return self._fibonacci(n - 1) + self._fibonacci(n - 2)
    
    async def async_retry_with_backoff(
        self,
        func: Callable[..., T],
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        exceptions: tuple = (Exception,)
    ) -> T:
        """Async version of retry with backoff"""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await func()
            except exceptions as e:
                last_exception = e
                
                if attempt == max_retries:
                    self.logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}")
                    raise e
                
                delay = self._calculate_delay(attempt, base_delay, max_delay, strategy)
                self.logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def handle_critical_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle critical errors with recovery actions"""
        self.logger.error(f"Critical error in {context.get('operation', 'unknown')}: {error}")
        
        recovery_actions = {
            "operation": context.get('operation', 'unknown'),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": time.time(),
            "recovery_attempted": True,
            "suggested_actions": self._get_suggested_actions(error, context)
        }
        
        return recovery_actions
    
    def _get_suggested_actions(self, error: Exception, context: Dict[str, Any]) -> list:
        """Get suggested recovery actions based on error type"""
        suggestions = []
        
        if "connection" in str(error).lower():
            suggestions.append("Check network connectivity")
            suggestions.append("Verify API endpoints are accessible")
        elif "timeout" in str(error).lower():
            suggestions.append("Increase timeout settings")
            suggestions.append("Check system resources")
        elif "authentication" in str(error).lower():
            suggestions.append("Verify API credentials")
            suggestions.append("Check token expiration")
        else:
            suggestions.append("Review error logs for details")
            suggestions.append("Contact system administrator")
        
        return suggestions
    
    def create_circuit_breaker(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """Create a circuit breaker pattern"""
        class CircuitBreaker:
            def __init__(self):
                self.failure_count = 0
                self.failure_threshold = failure_threshold
                self.recovery_timeout = recovery_timeout
                self.last_failure_time = 0
                self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
            
            def call(self, func: Callable[..., T], *args, **kwargs) -> T:
                if self.state == "OPEN":
                    if time.time() - self.last_failure_time > self.recovery_timeout:
                        self.state = "HALF_OPEN"
                    else:
                        raise Exception("Circuit breaker is OPEN")
                
                try:
                    result = func(*args, **kwargs)
                    if self.state == "HALF_OPEN":
                        self.state = "CLOSED"
                        self.failure_count = 0
                    return result
                except Exception as e:
                    self.failure_count += 1
                    self.last_failure_time = time.time()
                    
                    if self.failure_count >= self.failure_threshold:
                        self.state = "OPEN"
                    
                    raise e
        
        return CircuitBreaker() 