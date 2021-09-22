"""Main backend server and supporting methods."""

import asyncio
import datetime
import logging
from typing import Dict

import auraxium

from .blips import BaseControl, PlayerBlip
from ._db import DatabaseHandler
from ._map import MapHandler

log = logging.getLogger('backend')


class BackendServer:
    """Main backend server object.

    This class joins all of the individual components into a single
    object, mostly to facilitate cross-talk.

    Cross-module server functionality is to be implemented via methods
    of this class; the other modules are not mean to import each other.

    Attributes:
        arx_client: PS2 API client for synchronisation.
        db_handler: Database pool handler.
        map_handlers: Individual map handlers for each server

    """

    def __init__(self, arx_client: auraxium.Client,
                 db_handler: DatabaseHandler,
                 map_handlers: Dict[int, MapHandler]) -> None:
        self._is_active = True
        self.arx_client = arx_client
        self.db_handler = db_handler
        self.map_handlers = map_handlers
        # Register map handlers to receive blips
        try:
            listeners = db_handler.blip_listeners[BaseControl]
        except KeyError:
            listeners = []
        for handler in map_handlers.values():
            listeners.append(handler.dispatch_base_control)

        try:
            listeners = db_handler.blip_listeners[PlayerBlip]
        except KeyError:
            listeners = []
        for handler in map_handlers.values():
            listeners.append(handler.dispatch_player_blips)

    @property
    def is_active(self) -> bool:
        """Read-only flag for when the server is running."""
        return self._is_active

    async def async_init(self) -> None:
        """Asynchronous initialisation routine.

        This is similar in principle to :meth:`__init__()`, but must be
        called separately due to being a coroutine. This method must be
        called immediately after the regular initialiser every time.

        """
        await self.db_handler.async_init()
        loop = asyncio.get_running_loop()
        loop.create_task(self._database_scraper())

    async def _database_scraper(self) -> None:
        while self._is_active:
            last_run = datetime.datetime.now()
            await self.db_handler.fetch_blips()

            next_run = last_run + datetime.timedelta(seconds=5.0)
            delay = (next_run - datetime.datetime.now()).total_seconds()
            await asyncio.sleep(delay)

    async def close(self) -> None:
        """Close the backend server gracefully."""
        self._is_active = False
        await self.arx_client.close()
        # NOTE: The connection pool used may still process requests; any other
        # components must be shut down so the connections can be closed neatly
        # before the DB is disconnected.
        await self.db_handler.close()
