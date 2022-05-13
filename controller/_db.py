"""Database utility module.

This module provides type aliases and wrapper functions for any
database-driver-specific idiosyncracies and convnersions required.
"""

import typing

import psycopg
import psycopg_pool

T = typing.TypeVar('T')

# Type Aliases
Connection = psycopg.AsyncConnection[T]
Cursor = psycopg.AsyncCursor[T]
Pool = psycopg_pool.AsyncConnectionPool

# Exception aliases
ForeignKeyViolation = psycopg.errors.ForeignKeyViolation
UniqueViolation = psycopg.errors.UniqueViolation


def create_pool(host: str, port: int, user: str, password: str,
                database: str) -> Pool:
    """Create a new connection pool to the database.

    Args:
        host: Hostname of the database server.
        port: Port of the database server.
        user: Username to connect to the database.
        password: Password to connect to the database.
        database: Name of the database to connect to.

    """
    connection_string = (f'host={host} '
                         f'port={port} '
                         f'user={user} '
                         f'password={password} '
                         f'dbname={database}')
    return psycopg_pool.AsyncConnectionPool(connection_string)
