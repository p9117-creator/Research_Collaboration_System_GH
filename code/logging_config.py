"""
Structured Logging Configuration for Research Collaboration System
Implements structured JSON logging with multiple levels for production use
"""

import logging
import sys
import os
from datetime import datetime
from typing import Any, Dict, Optional
import json
import structlog
from functools import lru_cache


def add_timestamp(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add ISO timestamp to log events"""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_service_info(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add service metadata to log events"""
    event_dict["service"] = "research-collab-api"
    event_dict["version"] = os.getenv("APP_VERSION", "1.0.0")
    event_dict["environment"] = os.getenv("ENVIRONMENT", "development")
    return event_dict


def add_request_id(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add request ID for distributed tracing"""
    # This would typically come from middleware context
    import contextvars
    request_id_var = contextvars.ContextVar('request_id', default=None)
    request_id = request_id_var.get()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


class JSONRenderer:
    """Custom JSON renderer for structured logs"""
    
    def __call__(self, logger, method_name: str, event_dict: Dict[str, Any]) -> str:
        """Render log event as JSON string"""
        # Ensure all values are JSON serializable
        clean_dict = {}
        for key, value in event_dict.items():
            try:
                json.dumps(value)
                clean_dict[key] = value
            except (TypeError, ValueError):
                clean_dict[key] = str(value)
        
        return json.dumps(clean_dict, default=str, ensure_ascii=False)


@lru_cache()
def configure_logging(
    log_level: str = "INFO",
    json_format: bool = True,
    log_file: Optional[str] = None
) -> structlog.BoundLogger:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON format for logs (recommended for production)
        log_file: Optional file path for log output
    
    Returns:
        Configured structlog logger
    """
    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Shared processors for all loggers
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_timestamp,
        add_service_info,
        add_request_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Configure structlog
    if json_format:
        # JSON format for production
        structlog.configure(
            processors=shared_processors + [
                structlog.processors.format_exc_info,
                JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Console format for development
        structlog.configure(
            processors=shared_processors + [
                structlog.processors.format_exc_info,
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    # Configure standard logging
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        handlers.append(file_handler)
    
    logging.basicConfig(
        format="%(message)s",
        handlers=handlers,
        level=level,
    )
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    return structlog.get_logger()


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured structlog logger bound with the name
    """
    return structlog.get_logger(name)


class RequestLogger:
    """Middleware-compatible request logger"""
    
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or get_logger("request")
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        **extra
    ):
        """Log an HTTP request"""
        log_data = {
            "http_method": method,
            "http_path": path,
            "http_status": status_code,
            "duration_ms": round(duration_ms, 2),
            "event": "http_request",
        }
        
        if user_id:
            log_data["user_id"] = user_id
        if request_id:
            log_data["request_id"] = request_id
        
        log_data.update(extra)
        
        # Choose log level based on status code
        if status_code >= 500:
            self.logger.error(**log_data)
        elif status_code >= 400:
            self.logger.warning(**log_data)
        else:
            self.logger.info(**log_data)


class DatabaseLogger:
    """Logger for database operations"""
    
    def __init__(self, db_type: str, logger: Optional[structlog.BoundLogger] = None):
        self.db_type = db_type
        self.logger = logger or get_logger(f"database.{db_type}")
    
    def log_query(
        self,
        operation: str,
        collection: str,
        duration_ms: float,
        success: bool = True,
        error: Optional[str] = None,
        **extra
    ):
        """Log a database query"""
        log_data = {
            "db_type": self.db_type,
            "db_operation": operation,
            "db_collection": collection,
            "duration_ms": round(duration_ms, 2),
            "success": success,
            "event": "db_query",
        }
        
        if error:
            log_data["error"] = error
        
        log_data.update(extra)
        
        if success:
            self.logger.debug(**log_data)
        else:
            self.logger.error(**log_data)
    
    def log_connection(self, status: str, error: Optional[str] = None):
        """Log database connection status"""
        log_data = {
            "db_type": self.db_type,
            "connection_status": status,
            "event": "db_connection",
        }
        
        if error:
            log_data["error"] = error
            self.logger.error(**log_data)
        else:
            self.logger.info(**log_data)


class AuditLogger:
    """Logger for security audit events"""
    
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or get_logger("audit")
    
    def log_auth_event(
        self,
        event_type: str,  # login, logout, login_failed, token_refresh
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        reason: Optional[str] = None,
        **extra
    ):
        """Log authentication event"""
        log_data = {
            "audit_type": "authentication",
            "auth_event": event_type,
            "success": success,
            "event": "auth_audit",
        }
        
        if user_id:
            log_data["user_id"] = user_id
        if email:
            log_data["email"] = email
        if ip_address:
            log_data["ip_address"] = ip_address
        if reason:
            log_data["reason"] = reason
        
        log_data.update(extra)
        
        if success:
            self.logger.info(**log_data)
        else:
            self.logger.warning(**log_data)
    
    def log_access_event(
        self,
        resource: str,
        action: str,
        user_id: str,
        allowed: bool,
        role: Optional[str] = None,
        **extra
    ):
        """Log resource access event"""
        log_data = {
            "audit_type": "access_control",
            "resource": resource,
            "action": action,
            "user_id": user_id,
            "allowed": allowed,
            "event": "access_audit",
        }
        
        if role:
            log_data["role"] = role
        
        log_data.update(extra)
        
        if allowed:
            self.logger.debug(**log_data)
        else:
            self.logger.warning(**log_data)


# Initialize default logger on module import
def init_logging():
    """Initialize logging based on environment variables"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    json_format = os.getenv("LOG_FORMAT", "json").lower() == "json"
    log_file = os.getenv("LOG_FILE")
    
    configure_logging(
        log_level=log_level,
        json_format=json_format,
        log_file=log_file
    )


# Export commonly used items
__all__ = [
    'configure_logging',
    'get_logger',
    'init_logging',
    'RequestLogger',
    'DatabaseLogger',
    'AuditLogger',
]
