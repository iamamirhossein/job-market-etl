import logging.config

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(level: str = "INFO") -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": LOG_FORMAT,
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
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
