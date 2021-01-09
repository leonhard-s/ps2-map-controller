"""Population and player tracking components for APL."""

import datetime
import logging
from typing import Dict

log = logging.getLogger('backend.nsa')


class PlayerNSACorner:
    def __init__(self, id_: int, base_id: int) -> None:
        self.id = id_
        self.last_updated = self.last_absolute = datetime.datetime.now()

        self.position: Dict[int, float] = {}
        self.update_position(base_id)

    @property
    def since_absolute(self) -> datetime.timedelta:
        return datetime.datetime.now() - self.last_absolute

    @property
    def since_updated(self) -> datetime.timedelta:
        return datetime.datetime.now() - self.last_updated

    def collapse_position(self) -> int:
        """Return the most likely position for this player."""
        # NOTE: The following is only value for Python version 3.7 and higher
        # as dictionary key order is not guaranteed to be unique for earlier
        # versions of Python.
        affinity = list(self.position.values())
        highest_index = affinity.index(max(affinity))
        return list(self.position)[highest_index]

    def update_position(self, base_id: int) -> None:
        """Overwrite the current position with an known value.

        Calling this function implies that there is no doubt regarding
        the player's position. This generally means that the facility
        has just been defended or captured by the player.
        """
        self.position.clear()
        self.position[base_id] = 1.0


class NaniteSupervisionAgency:

    def __init__(self) -> None:
        # This dictionary stores the absolute position for each player
        self.players: Dict[int, PlayerNSACorner] = {}

    def absolute_position(self, base_id: int, id_: int, *args: int) -> None:
        player_ids = [id_, *args]
        for id_ in player_ids:
            try:
                self.players[id_].update_position(base_id)
            except KeyError:
                self.players[id_] = PlayerNSACorner(id_, base_id)

    def relative_position(self, player_a_id: int, player_b_id: int) -> None:
        try:
            player_a = self.players[player_a_id]
            player_b = self.players[player_b_id]
        except KeyError:
            return

        # Player has been seen in the last 30 seconds and is the more current
        if (player_a.since_absolute.total_seconds() < 30.0
                and player_a.last_absolute > player_b.last_absolute):
            # Move A to B
            target = player_b
            dest = player_a.collapse_position()
        elif (player_b.since_absolute.total_seconds() < 30.0
                and player_b.last_absolute > player_a.last_absolute):
            # Move B to A
            target = player_a
            dest = player_b.collapse_position()

        elif player_a.last_absolute < player_b.last_absolute:
            # Move B to A
            # TODO: Bias players
            target = player_a
            dest = player_b.collapse_position()

        else:
            # Move B to A
            # TODO: Bias players
            target = player_b
            dest = player_a.collapse_position()

        # Destination is already in the list of suspected positions
        if dest in target.position:
            log.debug('Collapsed player \'%d\' to base ID \'%d\'',
                      target.id, dest)
            target.update_position(dest)
        else:
            log.debug('')
        # target.update_position(dest.collapse_position())
        # log.debug('Moved player ')
