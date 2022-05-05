"""Utility module for the database driver.

This module contains any database-driver-specific functionality to keep
switching database drivers easy and error-free.
"""

import typing

import psycopg
import psycopg_pool

__all__ = [
    'Connection',
    'Cursor',
    'Pool',
    'create_pool',
    'ForeignKeyViolation',
]

Row = typing.TypeVar('Row')
Connection = psycopg.AsyncConnection[Row]
Cursor = psycopg.AsyncCursor[Row]
Pool = psycopg_pool.AsyncConnectionPool

# Errors
ForeignKeyViolation = psycopg.errors.ForeignKeyViolation


def create_pool(host: str, port: int, user: str, password: str,
                database: str) -> Pool:
    """Create a new connection pool to the database."""
    conn_str = (
        f'host={host} '
        f'port={port} '
        f'user={user} '
        f'password={password} '
        f'dbname={database}'
    )
    return Pool(conn_str)
