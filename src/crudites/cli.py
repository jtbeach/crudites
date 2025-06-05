"""Crudites CLI helper functions and decorators."""

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, Concatenate

import click
from pydantic_settings import BaseSettings

from .globals import AppGlobals


def async_cli_cmd[**P, T](
    func: Callable[P, Awaitable[T]],
) -> Callable[P, T]:
    """Decorator to run an async function/awaitable/coroutine in an event loop as a CLI command."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
        assert asyncio.iscoroutinefunction(func), (
            "async_cli_cmd can only be used on async functions"
        )
        return asyncio.run(func(*args, **kwargs))

    return wrapper


def inject_app_globals[AppGlobalsT: AppGlobals, ConfigT: BaseSettings, ReturnT, **P](
    app_globals_type: type[AppGlobalsT], config_type: type[ConfigT]
) -> Callable[
    [Callable[Concatenate[AppGlobalsT, P], Awaitable[ReturnT]]],
    Callable[P, Awaitable[ReturnT]],
]:
    """Decorator to inject app_globals instance into function as the first argument.

    The global instance is created using the `app_globals_type` class.
    When the function returns, the app_globals is destroyed and resources are cleaned up.
    """

    def decorator(
        func: Callable[Concatenate[AppGlobalsT, P], Awaitable[ReturnT]],
    ) -> Callable[P, Awaitable[ReturnT]]:
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> ReturnT:
            config = config_type()
            async with app_globals_type(config) as app_globals:
                rv = await func(app_globals, *args, **kwargs)
            return rv

        return async_wrapper

    return decorator


def crudites_command[AppGlobalsT: AppGlobals, ConfigT: BaseSettings, ReturnT, **P](
    app_globals_type: type[AppGlobalsT],
    config_type: type[ConfigT],
    *click_command_args: Any,
    **click_command_kwargs: Any,
) -> Callable[
    [Callable[Concatenate[AppGlobalsT, P], Awaitable[ReturnT]]],
    click.Command,
]:
    """Decorator on top of click.command to inject app_globals instance as the first argument and support async functions."""

    # The 'func' here is the *original* function written by the user.
    # It *must* expect the AppGlobalsType as its first argument,
    # as inject_app_globals will pass it.
    def decorator(
        func: Callable[Concatenate[AppGlobalsT, P], Awaitable[ReturnT]],
    ) -> click.Command:
        f_injected = inject_app_globals(app_globals_type, config_type)(func)
        f_async_ready = async_cli_cmd(f_injected)
        return click.command(*click_command_args, **click_command_kwargs)(f_async_ready)

    return decorator
