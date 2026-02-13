import logging
import json

logging.basicConfig(
    filename='brain_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_brain_action(user_id: str, segment: str, query: str, success: bool):
    status = "GRANTED" if success else "DENIED"
    logging.info("USER: %s | DEPT: %s | STATUS: %s | QUERY: %s",
                 user_id, segment, status, query[:50])

def log_audit_event(event_type: str, details: dict):
    """
    Log an audit event with structured details.

    Args:
        event_type: Type of event (e.g., "dataset.ingest")
        details: Dictionary containing event details
    """
    logging.info("EVENT: %s | DETAILS: %s", event_type, json.dumps(details))
