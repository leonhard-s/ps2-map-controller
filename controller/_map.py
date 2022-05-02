"""Map state definitions and map state handlers."""


import logging
from typing import Iterable, TypeVar

from .blips import Blip, PlayerBlip, BaseControl, RelativePlayerBlip

log = logging.getLogger('backend.map')

_BlipT = TypeVar('_BlipT', bound=Blip)


class ContinentInstance:
    """Continent-specific state handler for a given continent."""

    def __init__(self, continent_id: int) -> None:
        self.continent_id = continent_id
        self._base_owners: dict[int, int] = {}

    def clear(self) -> None:
        """Reset the continent handler.

        This clears all internal dictionaries, resetting the handler to
        the state it was in when it first started.
        """
        self._base_owners.clear()

    def process_base_control_blips(self, blips: Iterable[BaseControl]) -> None:
        """Event handler for :class:`BaseControl` blips.

        Args:
            blips (Iterable[BaseControl]): The blips to process

        """
        base_owners = self._base_owners
        for blip in blips:
            new_owner = blip.new_faction_id
            old_owner = base_owners[blip.old_faction_id]
            if old_owner == new_owner:
                log.warning('Received redundant ownership update for base ID '
                            '%d (was already %d before)',
                            blip.base_id, old_owner)
            else:
                log.debug('Updated ownership for base ID %d (was %d, now %d)',
                          blip.base_id, old_owner, new_owner)
                base_owners[blip.base_id] = new_owner

    def process_player_blips(self, blips: Iterable[PlayerBlip]) -> None:
        """Event handler for :class:`PlayerBlip` blips.

        Args:
            blips (Iterable[PlayerBlip]): The blips to process

        """
        log.info('Discarded %d absolute player blips', len(list(blips)))

    def process_relative_player_blips(
            self, blips: Iterable[RelativePlayerBlip]) -> None:
        """Event handler for :class:`RelativePlayerBlip` blips.

        Args:
            blips (Iterable[RelativePlayerBlip]): The blips to process

        """
        log.info('Discarded %d relative player blips', len(list(blips)))


class MapHandler:
    """Continent state manager for a given game server.

    This class keeps track of the state of the map for every continent
    on a given server. This includes facility captures, ownership, and
    the upcoming population model (NYI).

    """

    def __init__(self, server_id: int, continents: Iterable[int]) -> None:
        self.continents: dict[int, ContinentInstance] = {
            i: ContinentInstance(i) for i in continents}
        self.server_id = server_id

    def dispatch_base_control(self, blips: Iterable[BaseControl]) -> None:
        """Dispatch base control blips to the continent handler."""
        grouped = self._group_blips(blips)
        for continent_id, continent_blips in grouped.items():
            self.continents[continent_id].process_base_control_blips(
                continent_blips)
            log.info('Map handler for server %d processed %d blips for '
                     'continent %d',
                     self.server_id, len(continent_blips), continent_id)

    def dispatch_player_blips(self, blips: Iterable[PlayerBlip]) -> None:
        """Dispatch a series of player blips to the continent handler.

        This method is designed to be registered into the corresponding
        blip callback of the database component.

        Args:
            blips (Iterable[PlayerBlip]): The blips to dispatch.

        """
        grouped = self._group_blips(blips)
        for continent_id, continent_blips in grouped.items():
            self.continents[continent_id].process_player_blips(continent_blips)

    def clear(self) -> None:
        """Reset the map handler, destroying all map representations.

        This is mostly used to reset the state of the map handler
        for development or troubleshooting.

        """
        for continent in self.continents.values():
            continent.clear()

    def _group_blips(self, blips: Iterable[_BlipT]) -> dict[int, list[_BlipT]]:
        """Group the given blips by their continent ID.

        Additionally, this will discard any blips for other server IDs
        with a warning.

        Args:
            blips (Iterable[_BlipT]): The blips to group.

        Returns:
            dict[int, list[_BlipT]]: A dictionary mapping the map
            handler's valid continent IDs to blips that must be
            forwarded to that continent's state handler.

        """

        def is_valid(blip: _BlipT) -> bool:
            return blip.server_id == self.server_id

        filtered = filter(is_valid, blips)
        grouped: dict[int, list[_BlipT]] = {i: [] for i in self.continents}
        for blip in filtered:
            grouped[blip.continent_id].append(blip)
        return grouped
