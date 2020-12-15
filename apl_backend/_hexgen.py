"""Map hex generation utility.

This module makes the map hex coordinates available to the web app.
This process consists of the following steps.

1. Retrieving the hex coordinates of various bases through the PS2 API
2. Converting these hex coordinates into a set of hexagons defined in
   Cartesian coordinates
3. Merging these individual hexagons into a single continuous outline
   (i.e. a closed polygon)
4. Serialising this polygon's SVG representation

This serialised representation, along with the relative offset from the
global map origin, can then be stored in a database or on disk to be
accessed from the web app as needed.

"""

# NOTE: This entire module, particularly the code used to convert between the
# coordinate systems, was heavily inspired by the following article:
# <https://www.redblobgames.com/grids/hexagons/>
# Mad props to the author, the entire page is a masterpiece! <3

import math
from typing import Iterable, Iterator, List, NamedTuple, Set, Tuple

import auraxium


# pylint: disable=invalid-name
class _Point(NamedTuple):
    """Regular cartesian coordinates.

    This is just a glorified tuple.
    """

    x: float
    y: float


# pylint: disable=invalid-name
class _Tile(NamedTuple):
    """Internal coordinate system used for the PS2 map.

    This is a custom coordinate system using integer indices which is
    used to refer to individual hexes in the game's map view.

    Note that this coorinate system is not Cartesian; u and v are not
    perpendicular to each other. Instead, u faces to the right (like x
    for the Cartesian coordinates), but v faces up and to the right at
    a 60° angle.
    """

    # NOTE: This is comparable to the "Axial coordinates" mentioned in the
    # article raved about at the top of this module, except that the vectors
    # do not point in the same direction.
    # Just a few flipped signs on the coordinate conversions, though.

    u: int
    v: int


async def get_base_outline(client: auraxium.Client, base_id: int,
                           radius: float) -> List[Tuple[_Point, _Point]]:
    hexes = await client.find(
        auraxium.ps2.MapHex, results=1000, map_region_id=base_id)
    return _get_hexes_outline(
        [_Tile(h.data.x, h.data.y) for h in hexes], radius)


def _get_hex_corner(origin: _Point, radius: float, corner_idx: int) -> _Point:
    """Return a corner of a given hexagon.

    Corner indices are assigned counterclockwise with index 0 being the
    top right corner of the hexagon.

    Args:
        origin (_Point): Origin (i.e. midpoint) of the hexagon
        radius (float): Radius of the hexagon
        corner_idx (int): Corner index; 0 through 5

    Returns:
        _Point: Absolute position of the corner vertex

    Raises:
        ValueError: Raised if corner_idx is outside the [0; 5] interval
        ValueError: Raised if the radius is negative or zero

    """
    if radius <= 0.0:
        raise ValueError('radius must be greater than zero')
    if not 0 <= corner_idx <= 5:
        raise ValueError('corner index must be between 0 and 5')
    angle = math.radians(60 * corner_idx + 30)
    return _Point(origin.x + radius * math.cos(angle),
                  origin.y + radius * math.sin(angle))


def _get_hex_edge(origin: _Point, radius: float,
                  edge_idx: int) -> Tuple[_Point, _Point]:
    """Return an edge of a given hexagon.

    Edge indices are assigned counterclockwise with index 0 being the
    right edge of the hexagon.

    Args:
        origin (_Point): The origin of the hexagon
        radius (float): Radius of the hexagon
        edge_idx (int): The edge index of the hexagon

    Raises:
        ValueError: Raised if edge_idx is outside the [0; 5] interval
        ValueError: Raised if the radius is negative or zero

    Returns:
        Tuple[_Point, _Point]: A tuple of the two points of the edge

    """
    if radius <= 0.0:
        raise ValueError('radius must be greater than zero')
    if not 0 <= edge_idx <= 5:
        raise ValueError('edge index must be between 0 and 5')
    # Edge 0 ends with vertex 0. I just prefer the indices this way - too bad!
    start_idx = edge_idx - 1 if edge_idx != 0 else 5
    return (_get_hex_corner(origin, radius, start_idx),
            _get_hex_corner(origin, radius, edge_idx))


def _get_hex_neighbours(hex_: _Tile) -> Iterator[_Tile]:
    """Iterate over a hexagon's potential neighbours.

    This yields a series of tile coordinates.

    Args:
        hex_ (_Tile): The origin tile to walk around

    Yields:
        _Tile: An adjacent hexagonal tile

    """
    # NOTE: We could get clever with trigonometry here but that's slow and
    # introduces unnecessary floating point errors that we'd need to round back
    # out.
    yield _Tile(hex_.u+1, hex_.v)  # Right
    yield _Tile(hex_.u, hex_.v+1)  # Top right
    yield _Tile(hex_.u-1, hex_.v+1)  # Top left
    yield _Tile(hex_.u-1, hex_.v)  # Left
    yield _Tile(hex_.u, hex_.v-1)  # Bottom left
    yield _Tile(hex_.u+1, hex_.v-1)  # Bottom Right


def _get_hexes_outline(hexes: Iterable[_Tile],
                       radius: float) -> List[Tuple[_Point, _Point]]:
    """Return the exterior edges of the given list of tiles.

    This loops over every hex in the group and checks its neighbours
    for containment in the group. If the neighbours are not part of the
    input group, the edge is considered an exterior boundary and added
    to the output list.

    Args:
        hexes (Iterable[_Tile]): The list of hexes to outline
        radius (float): The radius of the hexagons

    Returns:
        List[Tuple[_Point, _Point]]: An unsorted list of exterior edges

    """
    # Create a cache of all hexes
    members: Set[_Tile] = set(hexes)
    # Create a list of all edges between member hexagons and those neighbours
    # that are not part of the group
    return [_get_hex_edge(_tile_to_point(h, radius), radius, i)
            for h in members for i, n in enumerate(_get_hex_neighbours(h))
            if n not in members]


def _radius_to_size(radius: float) -> Tuple[float, float]:
    """Return the width and height of a hexagon based on its radius.

    This should be really simple, but I regret to admit that I have
    messed this simple converison up way more times than I will
    immortalise in this docstring.

    Args:
        radius (float): The radius of the hexagon

    Returns:
        Tuple[float, float]: The width and height of the hexagon

    Raises:
        ValueError: Raised if the radius is negative or zero

    """
    if radius <= 0.0:
        raise ValueError('radius must be greater than zero')
    return math.sqrt(3) * radius, 2 * radius


def _tile_to_point(tile: _Tile, radius: float) -> _Point:
    """Return the point representation of a given tile.

    Args:
        tile (_Tile): The tile position to convert
        radius (float): Radius of the hexagonal tiles

    Returns:
        _Point: Cartesian position of the hexagon's origin

    Raises:
        ValueError: Raised if the radius is negative or zero

    """
    if radius <= 0.0:
        raise ValueError('radius must be greater than zero')
    width, height = _radius_to_size(radius)
    pos_x = width * (tile.u + tile.v * 0.5)
    pos_y = tile.v * height * 0.75
    return _Point(pos_x, pos_y)
