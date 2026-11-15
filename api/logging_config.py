"""Production JSON logging for the AgroCycle API.

Every log line is a single JSON object — machine-parseable by any log
aggregator (Loki, CloudWatch, Datadog, etc.) and still readable with
`docker logs agrocycle-api-1 | python3 -m json.tool`.

Fields on every line:
  ts          ISO-8601 UTC timestamp
  level       DEBUG / INFO / WARNING / ERROR / CRITICAL
  logger      logger name
  msg         human-readable message

Fields added by the request middleware:
  req_id      UUID4 hex (first 12 chars) — also sent as X-Request-ID header
  method      HTTP verb
  path        URL path (no query string)
  status      HTTP status code (integer)
  duration_ms round-trip time in milliseconds (integer)
  client_ip   real IP from X-Forwarded-For or direct connection

Fields added on ERROR:
  exc_type    exception class name
  exc_msg     exception message (single line)
  traceback   full traceback string
"""
from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import datetime, timezone


# Standard LogRecord attributes — anything else on the record came from extra={}
_STDLIB_KEYS = frozenset(logging.LogRecord(
    "", 0, "", 0, "", (), None
).__dict__.keys()) | {"message", "asctime"}


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Include every field injected via extra={} — not just a fixed allowlist.
        for key, value in record.__dict__.items():
            if key not in _STDLIB_KEYS and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            exc_type, exc_value, tb = record.exc_info
            payload["exc_type"] = exc_type.__name__ if exc_type else "Unknown"
            payload["exc_msg"] = str(exc_value)
            payload["traceback"] = "".join(traceback.format_exception(exc_type, exc_value, tb)).rstrip()

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure() -> None:
    """Call once at process startup — before any logging occurs."""
    formatter = _JsonFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Root logger: catches everything our code emits
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]

    # Redirect uvicorn's own loggers through the same formatter so the
    # format stays consistent.  We suppress the access log entirely
    # because our middleware already logs every request.
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers = [handler]
        lg.propagate = False

    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = False
