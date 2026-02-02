"""
Logging Configuration
Structured logging setup with Splunk integration support.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import traceback

from .config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": settings.ENVIRONMENT,
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

        # Add extra fields if present
        if hasattr(record, "session_id"):
            log_entry["session_id"] = record.session_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "intent"):
            log_entry["intent"] = record.intent
        if hasattr(record, "loan_type"):
            log_entry["loan_type"] = record.loan_type
        if hasattr(record, "decision"):
            log_entry["decision"] = record.decision
        if hasattr(record, "response_time_ms"):
            log_entry["response_time_ms"] = record.response_time_ms

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        return json.dumps(log_entry)


class ConversationLogger:
    """Specialized logger for conversation events."""

    def __init__(self):
        self.logger = logging.getLogger("conversation")

    def log_intent(
        self,
        session_id: str,
        intent: str,
        confidence: float,
        parameters: Dict[str, Any]
    ):
        """Log detected intent."""
        self.logger.info(
            f"Intent detected: {intent}",
            extra={
                "session_id": session_id,
                "intent": intent,
                "confidence": confidence,
                "parameters": parameters
            }
        )

    def log_eligibility_check(
        self,
        session_id: str,
        loan_type: str,
        decision: str,
        factors: Dict[str, Any],
        response_time_ms: float
    ):
        """Log eligibility decision."""
        self.logger.info(
            f"Eligibility check completed: {decision}",
            extra={
                "session_id": session_id,
                "loan_type": loan_type,
                "decision": decision,
                "factors": factors,
                "response_time_ms": response_time_ms
            }
        )

    def log_handoff(self, session_id: str, reason: str):
        """Log human agent handoff."""
        self.logger.info(
            f"Human handoff requested: {reason}",
            extra={
                "session_id": session_id,
                "handoff_reason": reason
            }
        )


def setup_logging():
    """Configure application logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return root_logger


# Initialize conversation logger
conversation_logger = ConversationLogger()
