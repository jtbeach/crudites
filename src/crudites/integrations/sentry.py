"""Sentry integration."""

import logging

import sentry_sdk
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SentryConfig(BaseModel):
    """Sentry configuration."""

    dsn: str | None = None
    environment: str | None = None
    release: str | None = None
    enabled: bool = False


def init_sentry(config: SentryConfig, integrations: list | None = None) -> None:
    """Init for Sentry."""
    if not config.enabled:
        logger.info("Skipping Sentry init since Sentry not enabled")
        return

    for name, value in (
        ("dsn", config.dsn),
        ("release", config.release),
        ("environment", config.environment),
    ):
        if not value:
            logger.warning("Skipping Sentry init since %s is missing", name)
            return

    if integrations is None:
        integrations = []

    logger.info("Initializing Sentry with environment: %s", config.environment)
    sentry_sdk.init(
        dsn=config.dsn,
        release=config.release,
        environment=config.environment,
        integrations=integrations,
        attach_stacktrace=True,
    )
