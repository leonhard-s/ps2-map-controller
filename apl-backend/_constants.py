import enum


class Faction(enum.IntEnum):
    """Enumerator for the game factions (aka. empires).

    Factions with non-matching IDs should not exist and will generally
    result in errors.

    """

    NONE = 0
    VS = 1
    NC = 2
    TR = 3
    NSO = 4

    @staticmethod
    def display_name(value: int) -> str:
        """Return the display name of a given faction.

        Args:
            value (int): The enum value of the faction.

        Raises:
            ValueError: Raised for invalid faction IDs.

        """
        names = ['None', 'Vanu Sovereignty', 'New Conglomerate',
                 'Terran Republic', 'Nanite Systems Operatives']
        try:
            return names[value]
        except IndexError as err:
            raise ValueError(f'Invalid faction ID \'{value}\'') from err

    @staticmethod
    def tag(value: int) -> str:
        """Return the tag of a given faction.

        Args:
            value (int): The enum value of the faction.

        Raises:
            ValueError: Raised for invalid faction IDs.

        """
        tags = ['N/A', 'VS', 'BC', 'TR', 'NSO']
        try:
            return tags[value]
        except IndexError as err:
            raise ValueError(f'Invalid faction ID \'{value}\'') from err


class Server(enum.IntEnum):
    """Enumerator for the game servers (aka. zones) recognised.

    Servers with non-matching IDs will be discarded with a warning.

    """

    CONNERY = 1
    MILLER = 10
    COBALT = 13
    EMERALD = 17
    BRIGGS = 25
    SOLTECH = 40


class Zone(enum.IntEnum):
    """Enumerator for the map zones (aka. continents) recognised.

    Zones with non-matching IDs will be discarded with an
    information-level logging message.

    """

    INDAR = 2
    HOSSIN = 4
    AMERISH = 6
    ESAMIR = 8
