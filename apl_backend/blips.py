"""The following is an enumeration of the event types sent.

These events are derived from PS2 API events, but have been stripped
back and merged to simplify the information contained.

"""

import datetime

import pydantic

__all__ = [
    'BaseControl',
    'PlayerBlip',
    'RelativePlayerBlip',
    'OutfitBlip'
]


class Blip(pydantic.BaseModel):  # pylint: disable=no-member
    """Base class for custom events ("Blips") used in APL.

    Any subclasses will be type-checked to ensure they match the type
    annotations.

    :param timestamp: UTC timestamp of the event
    :param server_id: ID of the server the event took place on
    :param continent_id: ID of the continent of the base

    """

    timestamp: datetime.datetime
    server_id: int
    continent_id: int

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


class BaseControl(Blip):
    """A facility has changed ownership.

    This includes continent (un-)locks and partially locked states.

    :param base_id: ID of the facility that changed ownership
    :param new_faction_id: Faction that gained control over the base
    :param old_faction_id: Faction that used to be in control

    """

    base_id: int
    new_faction_id: int
    old_faction_id: int
