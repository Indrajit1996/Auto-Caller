from collections.abc import Awaitable, Callable
from functools import wraps
from typing import TypeVar

from app.core.db import AsyncSessionLocal

T = TypeVar("T")


def with_async_db_session(
    func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    """
    Decorator for async functions that need a database session.

    If a session is provided as an argument, it will be used.
    Otherwise, a new session will be created and passed to the function.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        if "session" in kwargs and kwargs["session"] is not None:
            return await func(*args, **kwargs)
        else:
            async with AsyncSessionLocal() as session:
                kwargs["session"] = session
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    await session.rollback()
                    raise e

    return wrapper
