"""Tests for the AppGlobals class."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from pydantic_settings import BaseSettings

from crudites.globals import AppGlobals


class MockConfig(BaseSettings):
    """Test configuration class."""

    test_value: str = "test"


class MockResource:
    """Test resource class."""

    def __init__(self, name: str) -> None:
        """Constructor."""
        self.name = name
        self.initialized = False
        self.cleaned_up = False

    async def initialize(self) -> None:
        """Initialize the resource."""
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up the resource."""
        self.cleaned_up = True


class MockAppGlobals(AppGlobals[MockConfig]):
    """Test implementation of AppGlobals."""

    def __init__(self, config: MockConfig) -> None:
        """Constructor."""
        super().__init__(config)
        self.resource1: MockResource
        self.resource2: MockResource

    @property
    def resources(self) -> list[tuple[str, AsyncGenerator[Any, None]]]:
        """Test resources."""
        return [
            ("resource1", self._resource1_manager()),
            ("resource2", self._resource2_manager()),
        ]

    async def _resource1_manager(self) -> AsyncGenerator[MockResource, None]:
        """Resource 1 manager."""
        resource = MockResource("resource1")
        await resource.initialize()
        try:
            yield resource
        finally:
            await resource.cleanup()

    async def _resource2_manager(self) -> AsyncGenerator[MockResource, None]:
        """Resource 2 manager."""
        resource = MockResource("resource2")
        await resource.initialize()
        try:
            yield resource
        finally:
            await resource.cleanup()


async def test_app_globals_initialization() -> None:
    """Test basic initialization of AppGlobals."""
    config = MockConfig()
    app_globals = MockAppGlobals(config)
    assert app_globals.config == config


async def test_app_globals_context_manager() -> None:
    """Test AppGlobals as a context manager."""
    config = MockConfig()
    async with MockAppGlobals(config) as app_globals:
        assert isinstance(app_globals.resource1, MockResource)
        assert isinstance(app_globals.resource2, MockResource)
        assert app_globals.resource1.initialized
        assert app_globals.resource2.initialized
        assert not app_globals.resource1.cleaned_up
        assert not app_globals.resource2.cleaned_up

    # After context manager exits
    assert app_globals.resource1.cleaned_up
    assert app_globals.resource2.cleaned_up


async def test_app_globals_resource_cleanup_order() -> None:
    """Test that resources are cleaned up in reverse order."""
    cleanup_order: list[str] = []

    class OrderedTestAppGlobals(AppGlobals[MockConfig]):
        def __init__(self, config: MockConfig) -> None:
            super().__init__(config)
            self.resource1: MockResource
            self.resource2: MockResource

        @property
        def resources(self) -> list[tuple[str, AsyncGenerator[Any, None]]]:
            return [
                ("resource1", self._resource1_manager()),
                ("resource2", self._resource2_manager()),
            ]

        async def _resource1_manager(self) -> AsyncGenerator[MockResource, None]:
            resource = MockResource("resource1")
            await resource.initialize()
            try:
                yield resource
            finally:
                cleanup_order.append("resource1")
                await resource.cleanup()

        async def _resource2_manager(self) -> AsyncGenerator[MockResource, None]:
            resource = MockResource("resource2")
            await resource.initialize()
            try:
                yield resource
            finally:
                cleanup_order.append("resource2")
                await resource.cleanup()

    config = MockConfig()
    async with OrderedTestAppGlobals(config):
        pass

    assert cleanup_order == ["resource2", "resource1"]


async def test_app_globals_cleanup_on_error() -> None:
    """Test that resources are cleaned up even when an error occurs."""
    config = MockConfig()
    try:
        async with MockAppGlobals(config) as app_globals:
            assert app_globals.resource1.initialized
            assert app_globals.resource2.initialized
            raise ValueError("Test error")
    except ValueError:
        pass

    assert app_globals.resource1.cleaned_up
    assert app_globals.resource2.cleaned_up


async def test_app_globals_cleanup_error_handling() -> None:
    """Test error handling during resource cleanup."""

    class ErrorTestAppGlobals(AppGlobals[MockConfig]):
        def __init__(self, config: MockConfig) -> None:
            super().__init__(config)
            self.resource: MockResource

        @property
        def resources(self) -> list[tuple[str, AsyncGenerator[Any, None]]]:
            return [("resource", self._resource_manager())]

        async def _resource_manager(self) -> AsyncGenerator[MockResource, None]:
            resource = MockResource("resource")
            await resource.initialize()
            try:
                yield resource
            finally:
                try:
                    raise ValueError("Cleanup error")
                finally:
                    await resource.cleanup()

    config = MockConfig()
    async with ErrorTestAppGlobals(config) as app_globals:
        assert app_globals.resource.initialized

    # The error during cleanup should be logged but not propagated
    assert app_globals.resource.cleaned_up


def test_app_globals_abstract_method() -> None:
    """Test that AppGlobals cannot be instantiated without implementing resources."""
    config = MockConfig()
    with pytest.raises(TypeError):
        AppGlobals(config)  # type: ignore
