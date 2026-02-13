import logging
from datetime import datetime

logging.basicConfig(
    filename='brain_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_brain_action(user_id: str, segment: str, query: str, success: bool):
    status = "GRANTED" if success else "DENIED"
    logging.info(f"USER: {user_id} | DEPT: {segment} | STATUS: {status} | QUERY: {query[:50]}")