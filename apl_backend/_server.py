"""Main backend server and supporting methods."""

import asyncio
import datetime
import logging
import auraxium

from ._db import DatabaseHandler

log = logging.getLogger('backend')


class BackendServer:
    """Main backend server object for APL.

    This class joins all of the individual components into a single
    object, mostly to facilitate cross-talk.

    Cross-module server functionality is to be implemented via methods
    of this class; the other modules are not mean to import each other.

    Attributes:
        is_active: Flag for when the server is running.
        arx_client: PS2 API client for synchronisation.
        db_handler: Database pool handler.

    """

    def __init__(self, arx_client: auraxium.Client,
                 db_handler: DatabaseHandler) -> None:
        self.is_active = True
        self.arx_client = arx_client

        # TODO: Validate that ARX and the API are up and healthy

        self.db_handler = db_handler

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
        while self.is_active:
            last_run = datetime.datetime.now()
            await self.db_handler.fetch_blips()
            # TODO: Do something with blips other than debug prints

            next_run = last_run + datetime.timedelta(seconds=5.0)
            delay = (next_run - datetime.datetime.now()).total_seconds()
            await asyncio.sleep(delay)

    async def close(self) -> None:
        """Close the backend server gracefully."""
        self.is_active = False
        await self.arx_client.close()
        # NOTE: The connection pool used may still process requests; any other
        # components must be shut down first.
        await self.db_handler.close()