import structlog
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

# Configure standard logging to interface with structlog
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("dokter_penjaga.audit")

class AuditLogger:
    """
    Handles structured JSON audit logging.
    Complies with OPS-01 and PII-03.
    Ensures that only redacted/safe data is logged.
    """
    
    @staticmethod
    def log_request(session_id: str, redacted_query: str, metadata: Optional[Dict[str, Any]] = None):
        """Logs an incoming user request (after PII redaction)."""
        logger.info(
            "INCOMING_REQUEST",
            session_id=session_id,
            query=redacted_query,
            metadata=metadata or {}
        )

    @staticmethod
    def log_triage(session_id: str, is_emergency: bool, reason: str, confidence: float):
        """Logs the result of the triage classifier."""
        logger.info(
            "TRIAGE_RESULT",
            session_id=session_id,
            is_emergency=is_emergency,
            reason=reason,
            confidence=confidence
        )

    @staticmethod
    def log_guardrail_block(session_id: str, redacted_query: str, reason: str):
        """Logs when a guardrail blocks a request (e.g., prompt injection)."""
        logger.warning(
            "BLOCKED_INJECTION",
            session_id=session_id,
            query=redacted_query,
            reason=reason
        )

    @staticmethod
    def log_retrieval(session_id: str, retrieved_docs_count: int, sources: list):
        """Logs the documents retrieved from the vector database."""
        logger.info(
            "DOCUMENTS_RETRIEVED",
            session_id=session_id,
            count=retrieved_docs_count,
            sources=sources
        )

    @staticmethod
    def log_response(session_id: str, response_length: int, processing_time_ms: int):
        """Logs the final response generation metadata."""
        logger.info(
            "RESPONSE_GENERATED",
            session_id=session_id,
            response_length=response_length,
            processing_time_ms=processing_time_ms
        )

audit_logger = AuditLogger()
