import logging
import time
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
import sys
from pathlib import Path


class RequestIDFilter(logging.Filter):
    """Add request ID to log records."""
    
    def filter(self, record):
        record.request_id = getattr(record, 'request_id', 'no-request')
        return True


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    """
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class RequestLogger:
    """
    Request logging utility with structured logging support.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('request_logger')
        
        # Sensitive fields to mask in logs
        self.sensitive_fields = {
            'password', 'token', 'authorization', 'cookie', 'secret',
            'key', 'credential', 'auth', 'pass', 'pwd'
        }
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """Recursively mask sensitive data in dictionaries."""
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                    masked[key] = "***MASKED***"
                else:
                    masked[key] = self._mask_sensitive_data(value)
            return masked
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data
    
    def _get_client_info(self, request: Request) -> Dict[str, str]:
        """Extract client information from request."""
        return {
            'client_ip': self._get_client_ip(request),
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'referer': request.headers.get('referer', ''),
            'host': request.headers.get('host', ''),
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else 'unknown'
    
    async def _get_request_body(self, request: Request) -> Optional[Dict]:
        """Safely get request body."""
        try:
            if request.headers.get('content-type', '').startswith('application/json'):
                body = await request.body()
                if body:
                    json_body = json.loads(body.decode())
                    return self._mask_sensitive_data(json_body)
        except Exception as e:
            self.logger.warning(f"Failed to parse request body: {e}")
        return None
    
    def log_request_start(self, request: Request, request_id: str):
        """Log request start."""
        client_info = self._get_client_info(request)
        
        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                'request_id': request_id,
                'extra_fields': {
                    'event': 'request_start',
                    'method': request.method,
                    'path': request.url.path,
                    'query_params': dict(request.query_params),
                    **client_info
                }
            }
        )
    
    def log_request_end(
        self, 
        request: Request, 
        response: Response, 
        request_id: str, 
        duration: float,
        request_body: Optional[Dict] = None
    ):
        """Log request completion."""
        client_info = self._get_client_info(request)
        
        log_level = logging.INFO
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        
        extra_fields = {
            'event': 'request_end',
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            'response_size': response.headers.get('content-length', 'unknown'),
            **client_info
        }
        
        # Add request body for POST/PUT/PATCH requests
        if request_body and request.method in ['POST', 'PUT', 'PATCH']:
            extra_fields['request_body'] = request_body
        
        self.logger.log(
            log_level,
            f"Request completed: {request.method} {request.url.path} - "
            f"{response.status_code} ({duration*1000:.2f}ms)",
            extra={
                'request_id': request_id,
                'extra_fields': extra_fields
            }
        )
    
    def log_error(self, request: Request, request_id: str, error: Exception):
        """Log request error."""
        client_info = self._get_client_info(request)
        
        self.logger.error(
            f"Request error: {request.method} {request.url.path} - {str(error)}",
            exc_info=True,
            extra={
                'request_id': request_id,
                'extra_fields': {
                    'event': 'request_error',
                    'method': request.method,
                    'path': request.url.path,
                    'error_type': type(error).__name__,
                    'error_message': str(error),
                    **client_info
                }
            }
        )


# Global request logger
request_logger = RequestLogger()


async def logging_middleware(request: Request, call_next):
    """
    Logging middleware for FastAPI.
    """
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Skip logging for health check and static files
    if request.url.path in ['/health', '/favicon.ico']:
        return await call_next(request)
    
    # Log request start
    request_logger.log_request_start(request, request_id)
    
    # Get request body for logging (if applicable)
    request_body = None
    if request.method in ['POST', 'PUT', 'PATCH']:
        try:
            # Store original body for potential re-reading
            body = await request.body()
            request._body = body
            if body:
                json_body = json.loads(body.decode())
                request_body = request_logger._mask_sensitive_data(json_body)
        except Exception:
            pass
    
    start_time = time.time()
    
    try:
        # Process request
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log successful request
        request_logger.log_request_end(
            request, response, request_id, duration, request_body
        )
        
        return response
        
    except Exception as error:
        duration = time.time() - start_time
        
        # Log error
        request_logger.log_error(request, request_id, error)
        
        # Re-raise the error
        raise error


def setup_logging(app: FastAPI, log_level: str = "INFO"):
    """
    Setup comprehensive logging for FastAPI application.
    """
    # Determine if we're in development
    is_development = getattr(app, 'debug', False)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=[]
    )
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Setup formatters
    json_formatter = JSONFormatter()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
    )
    
    # Console handler (for development)
    if is_development:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(RequestIDFilter())
        console_handler.setLevel(logging.DEBUG)
    else:
        # JSON console handler for production
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(json_formatter)
        console_handler.addFilter(RequestIDFilter())
        console_handler.setLevel(logging.INFO)
    
    # File handlers
    # General application logs
    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_handler.setFormatter(json_formatter)
    app_handler.addFilter(RequestIDFilter())
    app_handler.setLevel(logging.INFO)
    
    # Error logs
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setFormatter(json_formatter)
    error_handler.addFilter(RequestIDFilter())
    error_handler.setLevel(logging.ERROR)
    
    # Request logs
    request_handler = logging.handlers.RotatingFileHandler(
        log_dir / "requests.log",
        maxBytes=50*1024*1024,  # 50MB
        backupCount=10
    )
    request_handler.setFormatter(json_formatter)
    request_handler.addFilter(RequestIDFilter())
    request_handler.setLevel(logging.INFO)
    
    # Configure loggers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    
    # Request logger specific handler
    request_logger_instance = logging.getLogger('request_logger')
    request_logger_instance.addHandler(request_handler)
    request_logger_instance.setLevel(logging.INFO)
    
    # Suppress noisy third-party loggers
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.error').setLevel(logging.INFO)
    logging.getLogger('fastapi').setLevel(logging.INFO)
    
    # Add logging middleware
    app.middleware("http")(logging_middleware)
    
    # Log startup
    logger = logging.getLogger(__name__)
    logger.info("Logging middleware configured", extra={
        'extra_fields': {
            'event': 'logging_setup',
            'log_level': log_level,
            'development_mode': is_development,
            'log_directory': str(log_dir.absolute())
        }
    })
    
    return logger


# Utility function to get logger with request context
def get_logger(name: str = None, request: Request = None) -> logging.Logger:
    """
    Get logger with request context.
    """
    logger = logging.getLogger(name or __name__)
    
    if request and hasattr(request.state, 'request_id'):
        # Create a logger adapter that adds request ID
        class RequestLoggerAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs):
                if 'extra' not in kwargs:
                    kwargs['extra'] = {}
                kwargs['extra']['request_id'] = request.state.request_id
                return msg, kwargs
        
        return RequestLoggerAdapter(logger, {})
    
    return logger


# Import this to add to your existing handlers
import logging.handlers