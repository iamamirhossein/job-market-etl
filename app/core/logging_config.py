import json
import logging
import logging.config
from datetime import UTC, datetime
from typing import Any, Literal

TEXT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

_STANDARD_ATTRS = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    """Render each log record as one line of JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS:
                payload[key] = value
        return json.dumps(payload, default=str)


def setup_logging(
    level: str = "INFO",
    log_format: Literal["text", "json"] = "text",
) -> None:
    formatter: dict[str, Any] = (
        {"()": JsonFormatter}
        if log_format == "json"
        else {"format": TEXT_FORMAT, "datefmt": "%Y-%m-%d %H:%M:%S"}
    )
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"default": formatter},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                },
            },
            "root": {"level": level, "handlers": ["console"]},
            "loggers": {
                "uvicorn": {"handlers": [], "level": level, "propagate": True},
                "uvicorn.error": {"handlers": [], "level": level, "propagate": True},
                "uvicorn.access": {"handlers": [], "level": level, "propagate": True},
            },
        }
    )
