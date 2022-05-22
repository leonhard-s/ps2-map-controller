"""Event dispatching component."""

import asyncio
import datetime
import logging
import typing

from .events import BaseControl, Event
from .abc import EventHandler
from ._db import Pool
from ._sql import SQL_POP_BASE_CONTROL

EventT = typing.TypeVar('EventT', bound=Event)


log = logging.getLogger('controller.dispatch')


class EventDispatcher:
    """Event dispatching instance.

    This class is responsible for taking chunks off the event buffer
    queue and dispatching them to the appropriate handlers.

    These handlers are invoked once for event type and origin server.
    """

    def __init__(self, pool: Pool) -> None:
        self._db_pool = pool
        self._handlers: list[EventHandler] = []

    def add_handler(self, handler: EventHandler) -> None:
        """Add a new event handler ot the dispatcher.

        The handler will be invoked once for each event type and origin
        server."""
        self._handlers.append(handler)

    async def run(self) -> None:
        """Run the dispatcher.

        This coroutine will run as long as the dispatcher is active and
        will only return on exception.
        """
        while True:
            await asyncio.sleep(1.0)
            events = await self._fetch_events()
            if events:
                log.debug('Fetched %d events from database', len(events))
                self._dispatch(events)

    def _dispatch(self, events: list[Event]) -> None:
        """Dispatch the provided events to all handlers.

        This groups the events by type and origin server and then
        invokes each handler for each combination of event type and
        server.
        """
        # Group events by type
        events_by_type: dict[type[Event], list[Event]] = {}
        for event in events:
            try:
                events_by_type[type(event)].append(event)
            except KeyError:
                events_by_type[type(event)] = [event]
        # For each event type, group by server and dispatch
        for type_, events_of_type in events_by_type.items():
            # If a key of this type exists, there must be at least one event
            log.debug('Dispatching %d events of type %s',
                      len(events_of_type), type_)
            # Group events by server
            events_by_server: dict[int, list[Event]] = {}
            for event in events_of_type:
                try:
                    events_by_server[event.server_id].append(event)
                except KeyError:
                    events_by_server[event.server_id] = [event]
            # Dispatch events to handlers
            for server_events in events_by_server.values():
                for handler in self._handlers:
                    handler.handle(server_events)

    @staticmethod
    def _event_factory(type_: type[EventT],
                       rows: list[tuple[typing.Any, ...]]) -> list[EventT]:
        """Factory method for creating events from database rows."""
        events: list[EventT] = []
        for row in rows:
            # Base
            args: list[typing.Any] = [
                datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S'),
                int(row[1]),
                int(row[2]),
            ]
            # Add additional args based on type
            if issubclass(type_, BaseControl):
                args.extend(map(int, row[3:6]))
            # Add instance
            events.append(type_(*args))
        return events

    async def _fetch_events(self, min_age: float = 1.0) -> list[Event]:
        """Fetch up to N events from the database's event buffer."""
        # Only fetch events that are at least min_age seconds old
        older_than = (
            datetime.datetime.now() - datetime.timedelta(seconds=min_age))
        events: list[Event] = []
        async with self._db_pool.connection() as conn:
            for type_, sql in self._get_event_types_sql():
                # NOTE: This should probably use a transaction to ensure we
                # don't lose any events if the fetch fails.
                async with conn.cursor() as cur:
                    await cur.execute(sql, (older_than,))
                    rows = [r[0] for r in await cur.fetchall()]
                events.extend(self._event_factory(type_, rows))
        return events

    @staticmethod
    def _get_event_types_sql() -> list[tuple[type[Event], str]]:
        """Return the SQL command for fetching a given event type."""
        return [
            (BaseControl, SQL_POP_BASE_CONTROL),
        ]
