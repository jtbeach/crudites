# Crudites

A modern Python package for building robust web applications with FastAPI and SQLAlchemy.
It focuses on providing the missing glue required to build standard CRUD applications. It
also offers a more opinionated view on how things should be done.

## Features

- **FastAPI Integration**: Built-in CORS configuration and middleware support
- **SQLAlchemy Integration**: Database configuration and connection pool management
- **Sentry Integration**: Error tracking and monitoring support
- **Type Safety**: Full type annotations and Pydantic models for configuration
- **Resource Management**: Automatic resource lifecycle management for FastAPI and CLI applications

## Installation

```bash
pip install crudites
```

## Quick Start

### FastAPI Setup

```python
import logging
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import Any

from brotli_asgi import BrotliMiddleware
from crudites.globals import AppGlobals
from crudites.integrations.fastapi import CorsConfig
from crudites.integrations.logging import LoggingConfig, init_logging
from crudites.integrations.sentry import SentryConfig, init_sentry
from crudites.integrations.sqlalchemy import DatabaseConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = logging.getLogger(__name__)

class Config(BaseSettings):
    # Environment variables are prefixed with MYAPP_ and the separator is __
    #  - MYAPP__LOGGING__FORMAT_AS_JSON=1
    #  - MYAPP__DATABASE__HOST=localhost
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="MYAPP__",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    cors: CorsConfig = CorsConfig()
    database: DatabaseConfig
    logging: LoggingConfig = LoggingConfig()
    sentry: SentryConfig = SentryConfig()


class MyAppGlobals(AppGlobals[Config]):
    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.db_engine: AsyncEngine

    @property
    def resources(self) -> Sequence[tuple[str, AsyncGenerator[Any, None]]]:
        return [("db_engine", self._db_engine_manager)]

    async def _db_engine_manager(self) -> AsyncGenerator[AsyncEngine, None]:
        logger.info("Setting up database engine...")
        try:
            engine = create_async_engine(self.config.database.sqlalchemy_url)
            yield engine
        finally:
            logger.info("Cleaning up database engine...")
            await engine.dispose()


@asynccontextmanager
async def lifespan(app: FastAPI):
    config: Config = app.state.CONFIG
    async with MyAppGlobals(config) as app_globals:
        app.state.APP_GLOBALS = app_globals
        yield

config = Config()

init_logging(config.logging)
init_sentry(config.sentry)

# Create the app
app = FastAPI(
    lifespan=lifespan,
    title="Hera Registration System API",
    version="1.0.0",
    description="Hera Registration System API",
)
app.state.CONFIG = config  # allow lifespan function to access config

# Add middleware
app.add_middleware(BrotliMiddleware)  # compress responses
app.add_middleware(CORSMiddleware, **config.cors.model_dump())  # setup CORS

# Add routes
```

### CLI Setup

```python
import logging
from collections.abc import AsyncGenerator, Sequence
from typing import Any

from crudites.cli import crudites_command
from crudites.globals import AppGlobals
from crudites.integrations.logging import LoggingConfig, init_logging
from crudites.integrations.sentry import SentryConfig, init_sentry
from crudites.integrations.sqlalchemy import DatabaseConfig
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = logging.getLogger(__name__)

class Config(BaseSettings):
    # Environment variables are prefixed with MYAPP_ and the separator is __
    #  - MYAPP__LOGGING__FORMAT_AS_JSON=1
    #  - MYAPP__DATABASE__HOST=localhost
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="MYAPP__",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    database: DatabaseConfig
    logging: LoggingConfig = LoggingConfig()
    sentry: SentryConfig = SentryConfig()


class MyAppGlobals(AppGlobals[Config]):

    db_engine: AsyncEngine

    @property
    def resources(self) -> Sequence[tuple[str, AsyncGenerator[Any, None]]]:
        return [("db_engine", self._db_engine_manager)]

    async def _db_engine_manager(self) -> AsyncGenerator[AsyncEngine, None]:
        logger.info("Setting up database engine...")
        try:
            engine = create_async_engine(self.config.database.sqlalchemy_url)
            yield engine
        finally:
            logger.info("Cleaning up database engine...")
            await engine.dispose()


@crudites_command(MyAppGlobals, Config)
async def cli(app_globals: MyAppGlobals):
    config = app_globals.config
    init_logging(config.logging)
    init_sentry(config.sentry)

    # Use the database engine from app_globals
    async with app_globals.db_engine.connect() as conn:
        # Do something with the connection
        pass
```

## Resource Management

Crudites provides a robust resource management system through `AppGlobals` and CLI command helpers. This system ensures proper initialization and cleanup of application resources like database connections, external services, and other global state.

### AppGlobals

`AppGlobals` is an abstract base class that manages the lifecycle of application resources. It implements the async context manager protocol for proper resource cleanup.

```python
from crudites.globals import AppGlobals
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

class MyAppGlobals(AppGlobals[MyConfig]):
    def __init__(self, config: MyConfig) -> None:
        super().__init__(config)
        self.db_engine: AsyncEngine

    @property
    def resources(self) -> Sequence[tuple[str, AsyncGenerator[Any, None]]]:
        return [("db_engine", self._db_engine_manager)]

    async def _db_engine_manager(self) -> AsyncGenerator[AsyncEngine, None]:
        logger.info("Setting up database engine...")
        try:
            engine = create_async_engine(self.config.sqlalchemy_url)
            yield engine
        finally:
            logger.info("Cleaning up database engine...")
            await engine.dispose()
```

#### FastAPI Integration

Use `AppGlobals` with FastAPI's lifespan:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    config: MyConfig = app.state.CONFIG
    async with MyAppGlobals(config) as app_globals:
        app.state.GLOBALS = app_globals
        yield

app = FastAPI(lifespan=lifespan)
```

### CLI Commands

The `crudites_command` decorator simplifies CLI command creation with proper resource management:

```python
from crudites.cli import crudites_command

@crudites_command(MyAppGlobals, MyConfig)
async def main(app_globals: MyAppGlobals):
    # Use app_globals.db_engine here
    async with app_globals.db_engine.connect() as conn:
        # Do something with the connection
        pass
```

Key features of the resource management system:
- Automatic resource initialization and cleanup
- Type-safe resource access
- Support for both FastAPI and CLI applications
- Async context manager support for clean resource lifecycle

## Development

### Prerequisites

This project uses [uv](https://github.com/astral-sh/uv) for dependency management and virtual environment handling. It's a fast Python package installer and resolver written in Rust.

### Installing uv

#### macOS / Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows
```powershell
powershell -c "(Invoke-WebRequest -Uri 'https://astral.sh/uv/install.ps1' -UseBasicParsing).Content | pwsh -Command -"
```

For more detailed installation instructions, visit the [uv documentation](https://github.com/astral-sh/uv#installation).

### Running all checks and test

```bash
poe all
```

### Formatting code (ruff)

```bash
uv run poe format
```

### Linting code (mypy, ruff, bandit)

```bash
uv run poe lint
```

To fix any auto-fixable errors

```bash
uv run poe fix
```

### Running tests

```bash
uv run poe test
```

To debug / target a single failing test and break in the debugger on exception

```bash
uv run poe debug_test tests/test_globals.py::test_app_globals_abstract_method
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
