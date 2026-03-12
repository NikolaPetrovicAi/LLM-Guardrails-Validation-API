import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime, UTC

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Standardizes logs in a JSON format for ELK/Datadog ingestion.
    """
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            # Standard ISO 8601 timestamp
            now = datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

def setup_logging(level=logging.INFO):
    """
    Global logging configuration to switch from text-based to JSON logs.
    """
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s %(request_id)s %(latency_ms)s %(cache_status)s'
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # Remove any existing handlers
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
        
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Prevent logs from bubbling up to root if not desired
    # but here we want to configure the root logger.
