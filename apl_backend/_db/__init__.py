"""Database wrapper and entity abstraction module.

This module acts as the translator between the Python data
representations and their database representations.

No SQL should live outside of this module.

"""

import asyncio
import datetime
import logging
from typing import (Any, Awaitable, Callable, Coroutine, Dict, Iterable, List,
                    Optional, Tuple, TypeVar, Union, cast)

import asyncpg
import pydantic
import tlru_cache

from ..blips import Blip, PlayerBlip

from ._types import Record

__all__ = [
    'DatabaseHandler'
]

_BlipT = TypeVar('_BlipT', bound=Blip)
_BlipCallback = Callable[[Iterable[_BlipT]], Union[None, Awaitable[None]]]
_BlipDispatchTable = Dict[_BlipT, List[_BlipCallback[_BlipT]]]

log = logging.getLogger('backend.database')


class DatabaseHandler:
    """Wrapper for Database interactions.

    This class implements methods that abstract database operations to
    use the blips and other object types used in the backend code.

    The :meth:`async_init()` method must be called immediately after
    the regular initialiser every time.

    Please note that :attr:`blip_listeners` is initialised as an empty
    list; the caller must manually register your callbacks for the
    appropriate blips after instantiation.

    :param pool: The connection pool to use for database interactions.
    :param blip_listeners: A mapping of blip types and their respective
        event listener callbacks.
    :type blip_listeners: Dict[Blip, List[BlipsCallback]]

    """

    def __init__(self, db_host: str, db_user: str,
                 db_pass: str, db_name: str) -> None:
        # Create a connection pool for the database connection
        log.info('Establishing database connection pool...')
        # NOTE: Connection pools handle reconnection internally, which saves us
        # the need to handle reconnections ourselves
        self.pool: asyncpg.pool.Pool = asyncpg.create_pool(  # type: ignore
            user=db_user, password=db_pass, database=db_name, host=db_host)
        self.blip_listeners: _BlipDispatchTable[Any] = {}

    async def async_init(self) -> None:
        """Asynchronous initialisation routine.

        This is similar in principle to :meth:`__init__()`, but must be
        called separately due to being a coroutine. This method must be
        called immediately after the regular initialiser every time.

        """
        await self.pool  # Calls the pool's asynchronous initialiser

    async def close(self) -> None:
        """Close the database handler and the underlying connection.

        This will wait for any underlying connections to be released
        before terminating the pool.
        """
        await self.pool.close()  # type: ignore

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
    async def get_base(self, base_id: int
                       ) -> Tuple[int, str, int, str, float, float]:
        """Retrieve a base by ID.

        This method is cached and safe to call repeatedly.

        :param base_id: The base ID to retrieve.

        :raise ValueError: Raised if the given base does not exist.

        """
        conn: asyncpg.Connection
        row: Optional[Record[str, Any]]
        async with self.pool.acquire() as conn:  # type: ignore
            row = await conn.fetchrow(  # type: ignore
                """--sql
                SELECT
                    ("id", "name", "continent_id", "type"::text,
                     "map_pos_x", "map_pos_y")
                FROM
                    "autopl"."Base"
                WHERE
                    "id" = $1
                ;""", base_id)
        if row is None:
            raise ValueError(f'Base ID not found: {base_id}')
        row_tuple: Tuple[int, str, int, str, float, float] = tuple(row)[0]
        log.debug('Cache miss: fetched base %d (%s) from database',
                  base_id, row_tuple[1])
        return row_tuple

    @tlru_cache.tlru_cache(maxsize=10, lifetime=3600.0)
    async def get_continents(self) -> List[Tuple[int, str]]:
        """Retrieve the list of servers.

        This method is cached and safe to call repeatedly.

        :param active_only: If True, only tracked servers are returned,
            by default True.

        """
        conn: asyncpg.Connection
        async with self.pool.acquire() as conn:  # type: ignore
            rows: List[Record[str, Any]] = await conn.fetch(  # type: ignore
                """--sql
                SELECT
                    ("id", "name")
                FROM
                    "autopl"."Continent"
                ;""")
        return [tuple(r)[0] for r in rows]

    @tlru_cache.tlru_cache(maxsize=20, lifetime=3600.0)
    async def get_servers(self, active_only: bool = True
                          ) -> List[Tuple[int, str, str]]:
        """Retrieve the list of servers.

        This method is cached and safe to call repeatedly.

        :param active_only: If True, only tracked servers are returned,
            by default True.

        """
        conn: asyncpg.Connection
        rows: List[Record[str, Any]]
        async with self.pool.acquire() as conn:  # type: ignore
            if active_only:
                rows = await conn.fetch(  # type: ignore
                    """--sql
                    SELECT
                        ("id", "name", "region")
                    FROM
                        "autopl"."Server"
                    WHERE
                        "tracking_enabled" = TRUE
                    ;""")
            else:
                rows = await conn.fetch(  # type: ignore
                    """--sql
                    SELECT
                        ("id", "name", "region")
                    FROM
                        "autopl"."Server"
                    ;""")
        return [tuple(r)[0] for r in rows]


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
