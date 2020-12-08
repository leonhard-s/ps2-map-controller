"""Database wrapper and entity abstraction module.

This module acts as the translator between the Python data
representations and their database representations.

No SQL should live outside of this module.

"""

import logging
from typing import Awaitable, Callable, Iterable, List, Union

import asyncpg

from ..blips import Blip

__all__ = [
    'DatabaseHandler'
]

BlipsCallback = Callable[[Iterable[Blip]], Union[None, Awaitable[None]]]

log = logging.getLogger('backend.database')


class DatabaseHandler:
    """Wrapper for Database interactions.

    This class implements methods that abstract database operations to
    use the blips and other object types used in the backend code.

    An event loop must already exist for the current thread when this
    class is instantiated.

    Please note that :attr:`blip_callback` is set to a dummy function
    by default, you must overwrite this attribute with your own
    dispatcher.

    :param pool: The connection pool to use for database interactions.
    :param blip_callback: A function or coroutine to call when new
        blips are processed.
    :type blip_callback: BlipsCallback

    """

    def __init__(self, db_host: str, db_user: str,
                 db_pass: str, db_name: str) -> None:
        # Create a connection pool for the database connection
        log.info('Establishing database connection pool...')
        # NOTE: Connection pools handle reconnection internally, which saves us
        # the need to handle reconnections ourselves
        self.pool: asyncpg.pool.Pool = asyncpg.create_pool(  # type: ignore
            user=db_user, password=db_pass, database=db_name, host=db_host)

        self.blip_listeners: List[BlipsCallback] = []
