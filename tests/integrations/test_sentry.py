"""Tests for Sentry integration."""

from unittest.mock import patch, MagicMock, Mock

from crudites.integrations.sentry import SentryConfig, init_sentry


def test_sentry_config_defaults() -> None:
    """Test SentryConfig default values."""
    config = SentryConfig()
    assert config.dsn is None
    assert config.environment is None
    assert config.release is None
    assert config.enabled is False


def test_sentry_config_custom_values() -> None:
    """Test SentryConfig with custom values."""
    config = SentryConfig(
        dsn="https://example.com", environment="test", release="1.0.0", enabled=True
    )
    assert config.dsn == "https://example.com"
    assert config.environment == "test"
    assert config.release == "1.0.0"
    assert config.enabled is True


@patch("crudites.integrations.sentry.sentry_sdk.init")
@patch("crudites.integrations.sentry.logger")
def test_init_sentry_when_disabled(mock_logger: Mock, mock_sentry_init: Mock) -> None:
    """Test init_sentry when Sentry is disabled."""
    config = SentryConfig(enabled=False)
    init_sentry(config)

    mock_logger.info.assert_called_once_with(
        "Skipping Sentry init since Sentry not enabled"
    )
    mock_sentry_init.assert_not_called()


@patch("crudites.integrations.sentry.sentry_sdk.init")
@patch("crudites.integrations.sentry.logger")
def test_init_sentry_when_missing_dsn(
    mock_logger: Mock, mock_sentry_init: Mock
) -> None:
    """Test init_sentry when DSN is missing."""
    config = SentryConfig(enabled=True, dsn=None)
    init_sentry(config)

    mock_logger.warning.assert_called_once_with(
        "Skipping Sentry init since %s is missing", "dsn"
    )
    mock_sentry_init.assert_not_called()


@patch("crudites.integrations.sentry.sentry_sdk.init")
@patch("crudites.integrations.sentry.logger")
def test_init_sentry_success(mock_logger: Mock, mock_sentry_init: Mock) -> None:
    """Test successful Sentry initialization."""
    config = SentryConfig(
        enabled=True, dsn="https://example.com", environment="test", release="1.0.0"
    )
    integrations = [MagicMock()]

    init_sentry(config, integrations)

    mock_logger.info.assert_called_once_with(
        "Initializing Sentry with environment: %s", "test"
    )
    mock_sentry_init.assert_called_once_with(
        dsn="https://example.com",
        release="1.0.0",
        environment="test",
        integrations=integrations,
        attach_stacktrace=True,
    )
