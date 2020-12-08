"""Database wrapper and entity abstraction module.

This module acts as the translator between the Python data
representations and their database representations.

No SQL should live outside of this module.

"""

import asyncio
import datetime
import logging
from typing import (Any, Awaitable, Callable, Coroutine, Dict, Iterable, List, Union,
                    cast)

import asyncpg
import pydantic
import tlru_cache

from ..blips import Blip, PlayerBlip

from ._types import Record

__all__ = [
    'DatabaseHandler'
]

BlipsCallback = Callable[[Iterable[Blip]], Union[None, Awaitable[None]]]

log = logging.getLogger('backend.database')


class DatabaseHandler:
    """Wrapper for Database interactions.

    This class implements methods that abstract database operations to
    use the blips and other object types used in the backend code.

    The :meth:`async_init()` method must be called immediately after
    the regular initialiser every time.

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

        self.blip_listeners: Dict[Blip, List[BlipsCallback]] = {}

    async def async_init(self) -> None:
        """Asynchronous initialisation routine.

        This is similar in principle to :meth:`__init__()`, but must be
        called separately due to being a coroutine. This method must be
        called immediately after the regular initialiser every time.

        """
        await self.pool  # Calls the pool's asynchronous initialiser

    async def fetch_blips(self, min_age: float = 5.0) -> None:
        """Extract and dispatch all recent blips.

        This will only return blips older than `min_age`. This is done
        to ensure that all related blips have been received for a given
        event.

        For example, facility captures emit both player-specific events
        used for population tracking, as well as a generic world event
        that holds information over the faction, capture time, and
        outfit affiliation. All of these events must be part of the
        same fetching cycle, which is why this minimum age constraint
        is crucial.

        The fetched blips are then dispatched to all blip listeners
        registered to the :attr:`blip_listeners` list.

        :param min_age: The minimum age of any blips to return.

        """
        # Get the most recent timestamp for which rows should be returned
        cutoff = datetime.datetime.now() - datetime.timedelta(seconds=min_age)
        blips: Dict[Blip, List[Any]] = {}

        conn: asyncpg.Connection
        async with self.pool.acquire() as conn:  # type: ignore

            blips[PlayerBlip] = await _get_player_blips(conn, cutoff)

        # Dispatch blips
        loop = asyncio.get_running_loop()
        for blip_type in Blip.__subclasses__():
            if blip_type not in self.blip_listeners:
                continue
            for blip_callback in self.blip_listeners[blip_type]:
                log.debug('Scheduling callback %s (%d) blips',
                          blip_callback.__name__, len(blips))
                if asyncio.iscoroutinefunction(blip_callback):
                    # The following line acts like an assignment at runtime; it
                    # only serves to appease static type checkers as they do not
                    # understand what "asyncio.iscoroutinefunction" does.
                    async_coro = cast(
                        Coroutine[Any, Any, None], blip_callback(blips))
                    loop.create_task(async_coro)
                else:
                    loop.call_soon(blip_callback, blips)

    @tlru_cache.tlru_cache(maxsize=100, lifetime=60.0)
    async def get_base(self, base_id: int) -> Any:
        """Retrieve a base by ID.

        This method is cached and safe to call repeatedly.

        :param base_id: The base ID to retrieve.

        :raise ValueError: Raised if the given base does not exist.

        """
        conn: asyncpg.Connection
        async with self.pool.acquire() as conn:  # type: ignore
            row: Record[str, Any] = await conn.fetchrow(  # type: ignore
                """--sql
                SELECT
                    *
                FROM
                    ps2."Base"
                WHERE
                    "id" = ?
                ;""", base_id)
        log.debug('Cache miss: fetched base %d (%s) from database',
                  base_id, row['name'])
        # TODO: Convert database record to class
        return row


async def _get_player_blips(conn: asyncpg.Connection,
                            cutoff: datetime.datetime) -> List[PlayerBlip]:
    rows: List[Record[str, Any]] = await conn.fetch(  # type: ignore
        # """--sql
        # DELETE FROM
        #     blips."PlayerBlip"
        # WHERE
        #     "timestamp" < $1
        # RETURNING
        #     *
        # ;""", cutoff)
        """--sql
                SELECT
                    *
                FROM
                    blips."PlayerBlip"
                WHERE
                    "timestamp" < $1
                ;""", cutoff)
    log.debug('Fetched %d blips from database', len(rows))

    blips: List[PlayerBlip] = []
    failed: List[Record[str, Any]] = []
    for row in rows:
        try:
            blips.append(PlayerBlip(**row))
        except pydantic.ValidationError:
            failed.append(row)
    if failed:
        log.warning('Skipped %d invalid rows; first: %s',
                    len(failed), failed[0])
    return blips
