import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request_id if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Add execution_time_ms if present
        if hasattr(record, "execution_time_ms"):
            log_data["execution_time_ms"] = record.execution_time_ms

        # Add any extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance with structured JSON formatting.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger with JSON output
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def log_tool_call(logger: logging.Logger, tool_name: str, params: Dict[str, Any]) -> None:
    """
    Log a tool call with parameters.

    Args:
        logger: Logger instance
        tool_name: Name of the tool being called
        params: Tool parameters
    """
    logger.info(f"Tool call: {tool_name} - Params: {params}")


def log_api_request(logger: logging.Logger, endpoint: str, params: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an API request.

    Args:
        logger: Logger instance
        endpoint: API endpoint
        params: Request parameters
    """
    logger.info(f"API request: {endpoint} - Params: {params}")


def log_api_response(logger: logging.Logger, endpoint: str, success: bool, count: int = 0) -> None:
    """
    Log an API response.

    Args:
        logger: Logger instance
        endpoint: API endpoint
        success: Whether the request was successful
        count: Number of items returned
    """
    status = "success" if success else "failed"
    logger.info(f"API response: {endpoint} - Status: {status} - Count: {count}")
