"""Tests for cli.py decorators and CLI integration."""

import logging

import pytest
from click.testing import CliRunner
from pydantic_settings import BaseSettings

from crudites.cli import async_cli_cmd, crudites_command, inject_app_globals
from crudites.globals import AppGlobals
from crudites.integrations.logging import LoggingConfig, setup_logging

logger = logging.getLogger(__name__)


# --- Mocks for testing ---
class DummyConfig(BaseSettings):
    """Dummy config for testing CLI decorators."""

    value: str = "dummy"

    logging: LoggingConfig = LoggingConfig()


class DummyGlobals(AppGlobals[DummyConfig]):
    """Dummy AppGlobals for testing CLI decorators."""

    def __init__(self, config: DummyConfig) -> None:
        """Initialize DummyGlobals with a resource attribute."""
        super().__init__(config)
        self.resource: str = "not set"
        self.resource2: str = "not set"
        logging.basicConfig(
            level=logging.INFO, force=True
        )  # required so that logger.info messages from resource initialization are captured in stdout

    @property
    def resources(self):
        """Async generator yielding and cleaning up a dummy resource."""

        async def resource_gen():
            try:
                self.resource = "initialized"
                logger.info("Resource initialized")
                yield self.resource
            finally:
                self.resource = "cleaned up"
                logger.info("Resource cleaned up")

        async def resource_gen2():
            try:
                self.resource2 = "initialized"
                logger.info("Resource2 initialized")
                yield self.resource2
            finally:
                raise Exception("Error thrown in resource2 cleanup")

        return [("resource", resource_gen()), ("resource2", resource_gen2())]


# --- Tests for async_cli_cmd ---
def test_async_cli_cmd_runs_async_function():
    """Test that async_cli_cmd runs an async function in a sync context."""
    called = {}

    @async_cli_cmd
    async def my_async_func(x):
        called["x"] = x
        return x * 2

    result = my_async_func(3)
    assert result == 6
    assert called["x"] == 3


def test_async_cli_cmd_raises_on_non_async():
    """Test that async_cli_cmd raises if used on a non-async function."""

    def not_async(x):
        return x

    with pytest.raises(AssertionError):
        async_cli_cmd(not_async)(1)


# --- Tests for inject_app_globals ---
@pytest.mark.asyncio
async def test_inject_app_globals_injects_and_cleans_up():
    """Test that inject_app_globals injects globals and cleans up resources."""
    injected = {}

    @inject_app_globals(DummyGlobals, DummyConfig)
    async def func(globals_obj, y):
        injected["resource"] = globals_obj.resource
        return y + 1

    result = await func(10)
    assert result == 11
    assert injected["resource"] == "initialized"
    # After context, resource should be cleaned up
    # (resource is set to 'cleaned up' after context)
    config = DummyConfig()
    g = DummyGlobals(config)
    async with g:
        pass
    assert g.resource == "cleaned up"


# --- Tests for crudites_command ---
def test_crudites_command_click_integration():
    """Test that crudites_command creates a working Click command with injected globals."""
    runner = CliRunner()

    @crudites_command(DummyGlobals, DummyConfig)
    async def cli_cmd(globals_obj):
        setup_logging(globals_obj.config.logging)
        logger.info(f"Command executed with resource: {globals_obj.resource}")

    result = runner.invoke(cli_cmd, [])
    assert result.exit_code == 0
    assert "Resource initialized" in result.output
    assert "Command executed with resource: initialized" in result.output
    assert "Resource cleaned up" in result.output
    assert "Error during AppGlobals resource cleanup" in result.output
    assert "Error thrown in resource2 cleanup" in result.output
