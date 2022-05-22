"""Controller component for map base ownership."""

import asyncio
import datetime
import logging
import typing

import auraxium

from ..abc import EventHandler
from ..events import BaseControl, Event
from .._db import Pool
from .._sql import SQL_GET_CONTINENTS, SQL_GET_TRACKED_SERVERS


log = logging.getLogger('controller.base_ownership')


class BaseOwnershipController(EventHandler):
    """Controller class for map base ownership state.

    This class satisfies the EventHandler interface and is responsible
    for tracking the state of the map across all servers.
    """

    # NOTE: This class should be a singleton as it *must* be the sole
    # arbitor of who owns what.

    def __init__(self, pool: Pool, service_id: str) -> None:
        self.service_id = service_id
        self._db_pool = pool
        self._ownership_map: dict[
            int, dict[int, tuple[int, datetime.datetime]]] = {}
        self._initializing: bool = True
        asyncio.get_event_loop().create_task(self.__ainit__())

    async def __ainit__(self) -> None:
        """Asynchronous initializer."""
        await self._initialize()

    async def reinitialize(self) -> None:
        """Reinitialize the controller.

        This will clear all current base ownership information and
        synchronize to the Census API's ``map`` endpoint.

        In the meanwhile, all events received will be buffered and
        processed once the controller is re-initialized.
        """
        await self._initialize()

    def handle(self, events: list[Event]) -> None:
        if events and isinstance(events[0], BaseControl):
            self._set_base_ownership(
                events[0].server_id, typing.cast(list[BaseControl], events))

    async def _initialize(self) -> None:
        """Initialize the controller."""
        self._initializing = True

        # Query the database to get the list of tracked servers and continents
        servers, continents = await self._get_tracked_servers_and_continents()
        log.info('Initializing controller for %d servers and %d continents',
                 len(servers), len(continents))

        # Reset the ownership map
        self._ownership_map = {s: {} for s in servers}

        # Load the base ownership for each tracked server
        async with auraxium.Client(service_id=self.service_id) as client:
            # We can't query mutltiple in-game servers at once via the API,
            # so we'll have to loop over them one by one.
            for server_id in servers:
                log.info('Loading base ownership for server %d', server_id)
                data = await client.request(
                    self._build_map_state_query(server_id, continents))
                try:
                    self._set_base_ownership_from_census_data(server_id, data)
                except (KeyError, ValueError):
                    log.exception('Failed to load base ownership for '
                                  'server %d: %s', server_id, data)
        self._initializing = False
        log.info('Initialization complete')

    def _build_map_state_query(self, server_id: int,
                               continents: list[int]) -> auraxium.census.Query:
        """Build the query used to access a server's map state."""
        continents_str = ','.join(map(str, continents))
        return auraxium.census.Query(
            'map', 'ps2:v2', service_id=self.service_id,
            world_id=server_id, zone_ids=continents_str)

    async def _get_tracked_servers_and_continents(self) -> tuple[list[int], list[int]]:
        """Load the list of tracked servers and continents."""
        async with self._db_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_GET_TRACKED_SERVERS)
                servers = [row[0] for row in await cur.fetchall()]
                await cur.execute(SQL_GET_CONTINENTS)
                continents = [row[0] for row in await cur.fetchall()]
        return servers, continents

    def _set_base_ownership(self, server_id: int, events: list[BaseControl]) -> None:
        """Set the ownership of a base."""
        try:
            owner_map = self._ownership_map[server_id]
        except KeyError:
            log.warning('Received BaseControl event for unknown server %d',
                        server_id)
            return
        for event in events:

            try:
                owner_map[event.base_id] = event.new_faction_id, event.timestamp
            except KeyError:
                log.warning('Received BaseControl event for unknown base %d',
                            event.base_id)
                continue

    def _set_base_ownership_from_census_data(
            self, server_id: int, data: dict[str, typing.Any]) -> None:
        """Update base ownership for a given server using Census data.

        This method should only be called while the controller is
        initializing as it will overwrite potentially newer data
        received via the event streaming service.

        Args:
            server_id: The ID of the server to update.
            data: The Census data for the server.

        """
        # The object returned for map status queris is absolute insanity and
        # thinking about why it looks this way is a bad idea. "Too bad!""
        map_list: list[dict[str, dict[str, typing.Any]]] = data['map_list']

        # NOTE: Using current timestamp for now since we don't have a way to
        #       get the actual timestamp the base last changed.
        now = datetime.datetime.now()

        self._ownership_map[server_id] = {}
        for map_data in map_list:
            for row_entry in map_data['Regions']['Row']:
                row_data: dict[str, str] = row_entry['RowData']
                base_id = int(row_data['RegionId'])
                faction_id = int(row_data['FactionId'])
                self._ownership_map[server_id][base_id] = faction_id, now
