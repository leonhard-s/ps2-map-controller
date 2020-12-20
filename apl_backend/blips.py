"""The following is an enumeration of the event types sent.

These events are derived from PS2 API events, but have been stripped
back and merged to simplify the information contained.

"""

import datetime
from typing import Optional

import pydantic

__all__ = [
    'PlayerBlip',
    'RelativePlayerBlip',
    'OutfitBlip',
    'FacilityCapture',
    'FacilityDefence',
    'FacilityReset'
]


class Blip(pydantic.BaseModel):  # pylint: disable=no-member
    """Base class for custom events ("Blips") used in APL.

    Any subclasses will be type-checked to ensure they match the type
    annotations.

    :param timestamp: UTC timestamp of the event
    :param server_id: ID of the server the event took place on
    :param zone_id: ID of the continent of the base

    """

    timestamp: datetime.datetime
    server_id: int
    zone_id: int

    class Config:
        """Pydantic model configuration.

        This inner class is used to namespace the pydantic
        configuration options.
        """
        allow_mutation = False
        anystr_strip_whitespace = True


class PlayerBlip(Blip):
    """Player blips allow associating a character with a facility.

    These events are sent for facility captures and defences, and are
    therefore quite reliable - for a short while.

    :param player_id: Character to position
    :param base_id: Facility to position the character at

    """

    player_id: int
    base_id: int


class RelativePlayerBlip(Blip):
    """Relative player blips give relative positioning between players.

    This generally happens when players revive or kill each other. For
    kills, mines (both infantry and anti tank) are ignored.

    The order of the characters has no relevance. For consistency, the
    character with the lower character ID will always be character A.

    :param player_a_id: Player A of the relation
    :param player_b_id: Player B of the relation

    """

    player_a_id: int
    player_b_id: int


class OutfitBlip(Blip):
    """An outfit blip is used to position outfits with facilities.

    One outfit blip is sent for every member's player blip, with extra
    blips being sent when an outfit captures a facility in its name.

    :param outfit_id: Outfit to be blipped
    :param base_id: Facility to blip the outfit at

    """

    outfit_id: int
    base_id: int


class FacilityCapture(Blip):
    """A facility has been captured by an outfit.

    :param base_id: ID of the facility that was captured
    :param duration_held: Time that :attr:`old_faction` held the base for in seconds
    :param new_faction_id: Faction that captured the base
    :param old_faction_id: Faction that lost the base
    :param outfit_id: Capturing outfit, if any

    """

    base_id: int
    # duration_held: int
    new_faction_id: int
    old_faction_id: int
    outfit_id: Optional[int]


class FacilityDefence(Blip):
    """A facility has been defended by its current owner.

    :param base_id: ID of the facility that was defended
    :param faction_id: Faction that captured the base

    """

    base_id: int
    faction_id: int


class FacilityReset(Blip):
    """A facility has been reset to another owner.

    This occurs after downtime, or if a continent immediately reopens
    after locking due to high population.

    :param base_id: ID of the facility that was reset
    :param faction_id: New owner of the facility

    """

    base_id: int
    faction_id: int
