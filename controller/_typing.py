"""Type aliases and helpers for the map controller."""

import typing

import asyncpg

__all__ = [
    'Connection',
    'Pool',
]

# pylint: disable=unsubscriptable-object

Connection = asyncpg.Connection[typing.Any] | asyncpg.pool.PoolConnectionProxy[typing.Any]
Pool = asyncpg.pool.Pool[typing.Any]
