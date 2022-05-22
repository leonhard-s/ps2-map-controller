"""Representation of the event types received by the dispatcher."""

import dataclasses
import datetime


@dataclasses.dataclass(frozen=True)
class Event:
    """Base class for events received from the event buffer DB."""

    timestamp: datetime.datetime
    server_id: int
    continent_id: int


@dataclasses.dataclass(frozen=True)
class BaseControl(Event):
    """Event received when a base changes ownership."""

    base_id: int
    old_faction_id: int
    new_faction_id: int
