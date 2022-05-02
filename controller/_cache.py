"""Caching utilities for the controller.

These are primarily used to reduce the number of database queries.
"""

import time
import collections
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

T = TypeVar('T')
P = ParamSpec('P')

Coro = Callable[P, Coroutine[Any, Any, T]]
Args = tuple[Any, ...]
Kwargs = dict[str, Any]


def tlru_cache(maxsize: int = 128, ttl: float = 60.0
               ) -> Callable[[Coro[P, T]], Coro[P, T]]:
    """Tine aware least recently used cache decorator.

    This decorator largely mirrors the behaviour of
    functools.lru_cache(). However, it expects asynchronous decorator
    targets and takes a ttl parameter, which specifies the time to live
    of the cached value.
    """

    def decorator(func: Coro[P, T]) -> Coro[P, T]:
        cache: collections.OrderedDict[tuple[Args, Kwargs], tuple[T, float]]
        cache = collections.OrderedDict()

        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            nonlocal cache
            now = time.time()
            key: tuple[tuple[Any, ...], dict[str, Any]] = (args, kwargs)
            # Check for cache hit
            if key in cache:
                value, last_access = cache[key]
                # Check for cache expiration
                if last_access + ttl > now:
                    return value
            # Cache miss or expired
            value = await func(*args, **kwargs)
            cache[key] = value, now
            # Truncate cache if necessary
            if len(cache) > maxsize:
                cache.popitem()
            return value

        return wrapper

    return decorator
