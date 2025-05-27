"""Module exposing functions to manage global state within the application.

This should be used to manage things that you want to initialize once for the lifetime
of the application (or per command/test).
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Sequence
from types import TracebackType
from typing import Any, Generic, Self, TypeVar

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


ConfigType = TypeVar("ConfigType", bound=BaseSettings)


class AppGlobals(ABC, Generic[ConfigType]):
    """Application global variables.

    This class is used to store global variables for the application. This is is done
    to make it easier to mock these global variables in tests.

    It implements the async context manager protocol so that we can scope the lifetime
    of globals and do proper resource cleanup.

    It is designed to be usable by both FastAPI, pytest and CLI scripts.

    To use this class, you need to define a subclass of `AppGlobals` in your application
    that defines the resources that need to be initialized.

    To do this, you need to subclass AppGlobals[MyConfig] where `MyConfig` is the
    configuration class for your application.

    We manage each global by a "resource generator", which is a generator that yields
    the resource when it is ready. You need to implement the `resources` property to
    return a sequence of tuples, where the first element is the attribute name by which
    you want to access the resource on this class and the second element is a generator
    that yields the resource when it is ready.

    ```
    class MyAppGlobals(AppGlobals[MyConfig]):

        db_engine: AsyncEngine

        @property
        def resources(self) -> Sequence[tuple[str, AsyncGenerator[Any, None]]]:
            return [("db_engine", self._db_engine_manager)]

        async def _db_engine_manager(self) -> AsyncGenerator[AsyncEngine, None]:
            logger.info("Setting up database engine...")
            try:
                engine = create_async_engine(...)
                yield engine
            finally:
                logger.info("Cleaning up database engine...")
                await engine.dispose()
    ```

    In FastAPI, you would normally define a lifecycle function using the below,
    where `MyAppGlobals` is a subclass of `AppGlobals` that is defined in the
    application.

    ```
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        config: MyConfig = app.state.CONFIG
        async with MyAppGlobals(config) as app_globals:
            app.state.GLOBALS = app_globals
            yield

    app = FastAPI(lifespan=lifespan)
    ```

    In Click CLI commands, we use the `crudites_command` decorator to inject the
    `AppGlobals` instance as the first argument. That decorator accepts the type of
    the applications's AppGlobals subclass (`MyAppGlobals`) as an argument.
    ```
    @crudites_command(MyAppGlobals, MyConfig)
    async def main(app_globals: MyAppGlobals):
        ...
    ```
    """

    def __init__(self, config: ConfigType) -> None:
        """Constructor."""
        self.config = config
        # Private variable used to track generators that need to be cleaned up
        self._resource_generators: list[AsyncGenerator[Any, None]] = []

    async def __aenter__(self) -> Self:
        """Enter the async context manager."""
        logger.info("Entering AppGlobals...")

        assert (
            len(self._resource_generators) == 0
        )  # make sure we're not already in a context

        # Create the generator objects for each resource. Each
        # resource is expect to be a AsyncGenerator
        for attr_name, resource_generator in self.resources:
            self._resource_generators.append(resource_generator)
            resource = await anext(resource_generator)
            setattr(self, attr_name, resource)

        return self

    @property
    @abstractmethod
    def resources(
        self,
    ) -> Sequence[tuple[str, AsyncGenerator[Any, None]]]:
        """Resources to be initialized."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        """Exit the async context manager.

        Args:
            exc_type: The type of exception that was raised, if any.
            exc_value: The exception instance that was raised, if any.
            traceback: The traceback object, if any.
        """
        logger.info("Exiting AppGlobals...")

        # Iterate through the stored generator objects and close them
        # This will execute the cleanup code after the 'yield' in each generator
        for gen in reversed(
            self._resource_generators
        ):  # Close in reverse order of acquisition if dependencies exist
            try:
                await gen.aclose()
            except Exception as e:
                logger.exception("Error during AppGlobals resource cleanup: %s", e)

        self._resource_generators.clear()
        logger.info("AppGlobals exited successfully.")

        return None  # allow exception to propagate
