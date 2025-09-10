"""
Error handling utilities for WhatsApp Revenue Copilot
Provides centralized error handling, logging, and monitoring
"""

import logging
import traceback
from typing import Optional, Dict, Any
from functools import wraps
from datetime import datetime
import uuid


class CopilotError(Exception):
    """Base exception for copilot-specific errors"""
    
    def __init__(self, message: str, error_code: str = None, context: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "GENERAL_ERROR"
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()
        self.error_id = str(uuid.uuid4())
        super().__init__(self.message)

class AgentError(CopilotError):
    """Agent-specific errors"""
    pass

class IntegrationError(CopilotError):
    """External integration errors (Google, OpenAI, etc.)"""
    pass

class ValidationError(CopilotError):
    """Input validation errors"""
    pass

class ConfigurationError(CopilotError):
    """Configuration and setup errors"""
    pass


def handle_errors(error_type: type = CopilotError, default_response: Any = None):
    """
    Decorator for handling errors in agent functions
    
    Args:
        error_type: Type of error to catch and wrap
        default_response: Default response to return on error
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type as e:
                # Log the error
                logger = logging.getLogger(func.__module__)
                logger.error(f"Error in {func.__name__}: {str(e)}", extra={
                    "error_id": getattr(e, 'error_id', 'unknown'),
                    "error_code": getattr(e, 'error_code', 'UNKNOWN'),
                    "function": func.__name__,
                    "args": str(args)[:200],  # Limit log size
                    "kwargs": str(kwargs)[:200]
                })
                
                # Re-raise with additional context
                if hasattr(e, 'context'):
                    e.context.update({
                        "function": func.__name__,
                        "timestamp": datetime.now().isoformat()
                    })
                
                if default_response is not None:
                    return default_response
                raise
            except Exception as e:
                # Wrap unexpected errors
                error_id = str(uuid.uuid4())
                logger = logging.getLogger(func.__module__)
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}", extra={
                    "error_id": error_id,
                    "error_code": "UNEXPECTED_ERROR",
                    "function": func.__name__,
                    "traceback": traceback.format_exc()
                })
                
                wrapped_error = CopilotError(
                    message=f"Unexpected error in {func.__name__}: {str(e)}",
                    error_code="UNEXPECTED_ERROR",
                    context={
                        "function": func.__name__,
                        "original_error": str(e),
                        "error_id": error_id
                    }
                )
                
                if default_response is not None:
                    return default_response
                raise wrapped_error
        return wrapper
    return decorator


def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator for retrying functions on error with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Factor to multiply delay by for each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (IntegrationError, ConnectionError, TimeoutError) as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger = logging.getLogger(func.__module__)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
                        raise
                except Exception as e:
                    # Don't retry on other types of errors
                    raise
            
            # This shouldn't be reached, but just in case
            raise last_exception
        return wrapper
    return decorator


class ErrorReporter:
    """Centralized error reporting and monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def report_error(self, error: CopilotError, context: Optional[Dict[str, Any]] = None):
        """
        Report error to monitoring systems
        
        Args:
            error: The error to report
            context: Additional context information
        """
        error_data = {
            "error_id": error.error_id,
            "error_code": error.error_code,
            "message": error.message,
            "timestamp": error.timestamp,
            "context": {**error.context, **(context or {})}
        }
        
        # Log the error
        self.logger.error(f"Error reported: {error.error_code}", extra=error_data)
        
        # In production, you might send to external monitoring:
        # - Sentry for error tracking
        # - DataDog for metrics
        # - Slack/Teams for notifications
        # - Custom webhook for alerting
    
    def report_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Report custom metrics
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for the metric
        """
        self.logger.info(f"Metric: {metric_name}={value}", extra={
            "metric_name": metric_name,
            "metric_value": value,
            "metric_tags": tags or {}
        })


# Global error reporter instance
error_reporter = ErrorReporter()


def validate_input(schema: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple input validation
    
    Args:
        schema: Validation schema (simplified)
        data: Data to validate
        
    Returns:
        Validated data
        
    Raises:
        ValidationError: If validation fails
    """
    errors = []
    
    for field, rules in schema.items():
        if rules.get("required", False) and field not in data:
            errors.append(f"Missing required field: {field}")
            continue
        
        if field in data:
            value = data[field]
            
            # Type validation
            if "type" in rules:
                expected_type = rules["type"]
                if not isinstance(value, expected_type):
                    errors.append(f"Field {field} must be of type {expected_type.__name__}")
            
            # Length validation
            if "max_length" in rules and hasattr(value, "__len__"):
                if len(value) > rules["max_length"]:
                    errors.append(f"Field {field} exceeds maximum length of {rules['max_length']}")
            
            # Custom validation
            if "validator" in rules:
                try:
                    rules["validator"](value)
                except Exception as e:
                    errors.append(f"Field {field} validation failed: {str(e)}")
    
    if errors:
        raise ValidationError(
            message=f"Validation failed: {'; '.join(errors)}",
            error_code="VALIDATION_ERROR",
            context={"validation_errors": errors, "input_data": data}
        )
    
    return data


def safe_get(obj: Dict[str, Any], key: str, default: Any = None, required: bool = False):
    """
    Safely get value from dictionary with error handling
    
    Args:
        obj: Dictionary to get value from
        key: Key to retrieve
        default: Default value if key not found
        required: Whether the key is required
        
    Returns:
        Value from dictionary or default
        
    Raises:
        ValidationError: If required key is missing
    """
    if key not in obj:
        if required:
            raise ValidationError(
                message=f"Required key '{key}' not found",
                error_code="MISSING_REQUIRED_KEY",
                context={"key": key, "available_keys": list(obj.keys())}
            )
        return default
    
    return obj[key]


# Example usage schemas
LEAD_SCHEMA = {
    "name": {"type": str, "required": True, "max_length": 100},
    "company": {"type": str, "required": True, "max_length": 100},
    "intent": {"type": str, "required": False, "max_length": 500},
    "budget": {"type": str, "required": False, "max_length": 50}
}

QUESTION_SCHEMA = {
    "user_id": {"type": str, "required": True, "max_length": 100},
    "text": {"type": str, "required": True, "max_length": 2000}
}

SCHEDULE_SCHEMA = {
    "text": {"type": str, "required": True, "max_length": 500}
}


def setup_logging(log_level: str = "INFO"):
    """
    Setup structured logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    import json_logging
    
    # Enable json logging
    json_logging.init_non_web(enable_json=True)
    
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Custom formatter for development
    if log_level.upper() == "DEBUG":
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)


# Circuit breaker pattern for external services
class CircuitBreaker:
    """Simple circuit breaker implementation"""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Call function with circuit breaker protection"""
        if self.state == "OPEN":
            if datetime.now().timestamp() - self.last_failure_time > self.reset_timeout:
                self.state = "HALF_OPEN"
            else:
                raise IntegrationError(
                    message="Circuit breaker is OPEN",
                    error_code="CIRCUIT_BREAKER_OPEN"
                )
        
        try:
            result = func(*args, **kwargs)
            # Success - reset failure count
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now().timestamp()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise IntegrationError(
                message=f"Service call failed: {str(e)}",
                error_code="SERVICE_CALL_FAILED",
                context={"circuit_breaker_state": self.state}
            )


# Global circuit breakers for external services
openai_circuit_breaker = CircuitBreaker(failure_threshold=3, reset_timeout=30)
google_circuit_breaker = CircuitBreaker(failure_threshold=5, reset_timeout=60)
