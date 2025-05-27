"""Crudites CLI helper functions and decorators."""

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, Concatenate, ParamSpec, TypeVar

import click
from pydantic_settings import BaseSettings

from .globals import AppGlobals

AppGlobalsType = TypeVar("AppGlobalsType", bound=AppGlobals)
ConfigType = TypeVar("ConfigType", bound=BaseSettings)
ParamsType = ParamSpec("ParamsType")
ReturnType = TypeVar("ReturnType")


def async_cli_cmd(
    func: Callable[ParamsType, Awaitable[ReturnType]],
) -> Callable[ParamsType, ReturnType]:
    """Decorator to run an async function/awaitable/coroutine in an event loop as a CLI command."""

    @wraps(func)
    def wrapper(*args: ParamsType.args, **kwargs: ParamsType.kwargs) -> Any:
        assert asyncio.iscoroutinefunction(func), (
            "async_cli_cmd can only be used on async functions"
        )
        return asyncio.run(func(*args, **kwargs))

    return wrapper


def inject_app_globals(
    app_globals_type: type[AppGlobalsType], config_type: type[ConfigType]
) -> Callable[
    [Callable[Concatenate[AppGlobalsType, ParamsType], Awaitable[ReturnType]]],
    Callable[ParamsType, Awaitable[ReturnType]],
]:
    """Decorator to inject app_globals instance into function as the first argument.

    The global instance is created using the `app_globals_type` class.
    When the function returns, the app_globals is destroyed and resources are cleaned up.
    """

    def decorator(
        func: Callable[Concatenate[AppGlobalsType, ParamsType], Awaitable[ReturnType]],
    ) -> Callable[ParamsType, Awaitable[ReturnType]]:
        @wraps(func)
        async def async_wrapper(
            *args: ParamsType.args, **kwargs: ParamsType.kwargs
        ) -> ReturnType:
            config = config_type()
            async with app_globals_type(config) as app_globals:
                rv = await func(app_globals, *args, **kwargs)
            return rv

        return async_wrapper

    return decorator


def crudites_command(
    app_globals_type: type[AppGlobalsType],
    config_type: type[ConfigType],
    *click_command_args: Any,
    **click_command_kwargs: Any,
) -> Callable[
    [Callable[Concatenate[AppGlobalsType, ParamsType], Awaitable[ReturnType]]],
    click.Command,
]:
    """Decorator on top of click.command to inject app_globals instance as the first argument and support async functions."""

    # The 'func' here is the *original* function written by the user.
    # It *must* expect the AppGlobalsType as its first argument,
    # as inject_app_globals will pass it.
    def decorator(
        func: Callable[Concatenate[AppGlobalsType, ParamsType], Awaitable[ReturnType]],
    ) -> click.Command:
        f_injected = inject_app_globals(app_globals_type, config_type)(func)
        f_async_ready = async_cli_cmd(f_injected)
        return click.command(*click_command_args, **click_command_kwargs)(f_async_ready)

    return decorator
