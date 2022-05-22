"""Abstract base classes for the controller module."""

import abc

from .events import Event


class EventHandler(metaclass=abc.ABCMeta):
    """Class interface for event handlers.

    Event handlers may be registered to the event dispatcher and will
    be invoked once for each event type and origin server, each time
    with a list of events to observer.
    """

    @abc.abstractmethod
    def handle(self, events: list[Event]) -> None:
        """Handle a batch of events of a given type.

        Note that this is called multiple times for each event type.
        So while the `events` list can take on any event type, it will
        only contain one type of event per invocation.

        This means that checking the instance of the first element of
        the list is sufficient for sorting by event type.

        Additionally, this is called once for each server. So the
        ``server_id`` attribute of the events will be the same for all
        events in the list.
        """
        raise NotImplementedError()
