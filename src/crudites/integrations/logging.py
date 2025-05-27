"""Logging integration."""

import logging
import logging.config

import json_log_formatter
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    format_as_json: bool = False
    format_str: str | None = None
    level: str = "INFO"


def setup_logging(config: LoggingConfig) -> None:
    """Basic function to init logging."""
    if config.format_str is None:
        config.format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    dict_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {"format": config.format_str},
            "json": {"()": json_log_formatter.VerboseJSONFormatter},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": config.level,
                "formatter": "json" if config.format_as_json else "simple",
            }
        },
        "root": {"level": config.level, "handlers": ["console"]},
        "loggers": {
            "sqlalchemy.engine.Engine": {"propagate": False}
        },  # Hide duplicated sqlalchemy engine logs
    }

    logging.config.dictConfig(dict_config)
    msg = "Initialized app logging at level %s"
    logger.info(msg, config.level)
