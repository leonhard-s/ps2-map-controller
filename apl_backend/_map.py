"""Map state definitions and map state handlers."""


import logging
from typing import Dict, Iterable, List, TypeVar

from .blips import Blip, PlayerBlip

log = logging.getLogger('backend.map')

_BlipT = TypeVar('_BlipT', bound=Blip)


class ContinentInstance:
    """Continent-specific state handler for a given continent."""

    def __init__(self, continent_id: int) -> None:
        self.continent_id = continent_id

    def process_player_blips(self, blips: List[PlayerBlip]) -> None:
        log.debug('Discarded %d player blips (NYI)', len(blips))


class MapHandler:
    """Continent state manager for a given game server.

    This class keeps track of the state of the map for every continent
    on a given server. This includes facility captures, ownership, and
    the upcoming population model (NYI).

    """

    def __init__(self, server_id: int, continents: Iterable[int]) -> None:
        self.continents: Dict[int, ContinentInstance] = {
            i: ContinentInstance(i) for i in continents}
        self.server_id = server_id

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

    def _group_blips(self, blips: Iterable[_BlipT]) -> Dict[int, List[_BlipT]]:
        """Group the given blips by their continent ID.

        Additionally, this will discard any blips for other server IDs
        with a warning.

        Args:
            blips (Iterable[_BlipT]): The blips to group.

        Returns:
            Dict[int, List[_BlipT]]: A dictionary mapping the map
            handler's valid continent IDs to blips that must be
            forwarded to that continent's state handler.

        """

        def is_valid(blip: _BlipT) -> bool:
            return blip.server_id == self.server_id

        filtered = filter(is_valid, blips)
        grouped: Dict[int, List[_BlipT]] = {i: [] for i in self.continents}
        for blip in filtered:
            grouped[blip.zone_id].append(blip)
        return grouped
