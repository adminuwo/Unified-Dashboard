import re
from typing import Dict, Any, Optional
from pymongo.database import Database  # type: ignore

from src.database.models import LogEntry


def redact_message(message: str) -> str:
    """Redact sensitive patterns like JWT tokens and API keys from messages."""
    if not message:
        return message

    # Redact JWT tokens (Bearer eyJhbGciOi...) -> Bearer [REDACTED_JWT]
    message = re.sub(
        r"Bearer\s+[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=\.\+/]+",
        "Bearer [REDACTED_JWT]",
        message
    )
    # Also handle simpler or partial Bearer tokens
    message = re.sub(
        r"Bearer\s+[A-Za-z0-9\-_=\.\+/]+",
        "Bearer [REDACTED_JWT]",
        message
    )

    # Redact API keys starting with key_ (key_12345...) -> key_[REDACTED_API_KEY]
    message = re.sub(
        r"key_[a-zA-Z0-9_\-]+",
        "key_[REDACTED_API_KEY]",
        message
    )

    return message


def redact_metadata(metadata: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Recursively redact sensitive key-value pairs from metadata dictionary."""
    if metadata is None:
        return None
    if not isinstance(metadata, dict):
        return metadata

    redacted: Dict[str, Any] = {}
    sensitive_terms = ["password", "api_key", "access_token", "secret"]

    for k, v in metadata.items():
        k_lower = str(k).lower()
        if any(term in k_lower for term in sensitive_terms):
            redacted[k] = "[REDACTED_SENSITIVE_DATA]"
        elif isinstance(v, dict):
            redacted[k] = redact_metadata(v)
        elif isinstance(v, list):
            redacted[k] = [redact_metadata(item) if isinstance(item, dict) else item for item in v]
        else:
            redacted[k] = v

    return redacted


def create_log_entry(db: Database, application_id: str, log_in: Any) -> LogEntry:
    """Process, redact, and insert a new application log entry into MongoDB."""
    clean_msg = redact_message(log_in.message)
    clean_meta = redact_metadata(log_in.metadata)

    log_dict = LogEntry.create_dict(
        application_id=application_id,
        level=log_in.level.upper(),
        event=log_in.event,
        message=clean_msg,
        user_id=log_in.user_id,
        extra_metadata=clean_meta
    )

    db["logs"].insert_one(log_dict)
    return LogEntry(log_dict)
