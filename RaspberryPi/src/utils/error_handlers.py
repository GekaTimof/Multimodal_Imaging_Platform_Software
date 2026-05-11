"""
Error handling utilities for Raspberry Pi services.
Provides decorators and utilities for consistent error handling.
"""

import functools
import logging
import time
from typing import Any, Callable, Optional, Union, Tuple

logger = logging.getLogger(__name__)


def api_error_handler(func: Callable) -> Callable:
    """
    Decorator for API functions to handle common errors consistently.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Tuple[bool, Union[Any, str]]:
        try:
            result = func(*args, **kwargs)
            if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], bool):
                return result  # Already in expected format
            return True, result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            return False, str(e)
    
    return wrapper


def database_error_handler(func: Callable) -> Callable:
    """
    Decorator for database operations to handle SQLite errors.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with database error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"Database error in {func.__name__}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    return wrapper


def retry_on_failure(max_attempts: int = 3, 
                    delay: float = 1.0) -> Callable:
    """
    Decorator to retry function calls on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator


def validate_parameters(validation_func: Callable) -> Callable:
    """
    Decorator to validate function parameters.
    
    Args:
        validation_func: Function that takes args and kwargs and validates them
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            validation_result = validation_func(*args, **kwargs)
            if validation_result is not True:
                error_msg = f"Parameter validation failed for {func.__name__}: {validation_result}"
                logger.error(error_msg)
                return False, error_msg
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to log function execution time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with execution time logging
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    return wrapper


def safe_execute(default_return: Any = None, log_error: bool = True) -> Callable:
    """
    Decorator to safely execute functions and return default on error.
    
    Args:
        default_return: Default value to return on error
        log_error: Whether to log errors
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {e}")
                return default_return
        
        return wrapper
    return decorator


# Import config for retry decorator
try:
    from config import config
except ImportError:
    # Fallback values if config is not available
    class Config:
        RETRY_ATTEMPTS = 3
        RETRY_DELAY_SECONDS = 1.0
    config = Config()
