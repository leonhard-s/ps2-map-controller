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
from typing import Dict, Iterable, Iterator, List, NamedTuple, Set, Tuple

import auraxium
import svgwrite
from svgwrite.shapes import Polygon


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


async def get_base_outlines(client: auraxium.Client, continent_id: int,
                            radius: float) -> Dict[int, List[_Point]]:
    """Retrieve all base outlines for the given continent.

    This returns a mapping of base IDs to closed polygons representing
    that base's outline.

    Args:
        client (auraxium.Client): ARX client to use for requests
        continent_id (int): The continent/zone ID to access
        radius (float): Arbitrary scaling factor for hexes

    Returns:
        Dict[int, List[_Point]]: A mapping of base IDs to a polygon
            representing its outline.

    """
    # Get all hexes on this continent
    map_hexes = await client.find(
        auraxium.ps2.MapHex, results=10_000, zone_id=continent_id)
    # Group the hexes by their base ID
    base_tiles: Dict[int, List[_Tile]] = {}
    for hex_ in map_hexes:
        base_id = hex_.data.map_region_id
        try:
            base_tiles[base_id].append(_Tile(hex_.data.x, hex_.data.y))
        except KeyError:
            base_tiles[base_id] = [_Tile(hex_.data.x, hex_.data.y)]
    # Create the outlines for each base
    base_outlines: Dict[int, List[_Point]] = {}
    for base_id, hexes in base_tiles.items():
        # Get the map hex outlines for this base
        outlines = _get_hexes_outline(hexes, radius, 1e-2)
        # Connect the individual outlines into a single polygon
        base_outlines[base_id] = _connect_outlines(outlines)
    return base_outlines


async def get_base_svgs(client: auraxium.Client, continent_id: int,
                        radius: float) -> Dict[int, str]:
    """Creating a mapping of base IDs to serialised outline SVGs.

    This is the primary method exported by this module and allows
    generation of hex outlines for a given continent.

    These outlines are provided via serialised SVG elements containing
    a single closed polygon each.

    Args:
        client (auraxium.Client): The API client to use for the request
        continent_id (int): The ID of the continent to access
        radius (float): Outer radius of a single hexagon in pixels

    Returns:
        Dict[int, str]: A mapping of base IDs to its outline as a
            serialised SVG element

    """
    # Get the base outlines as closed polygons
    outlines = await get_base_outlines(client, continent_id, radius)
    # Create SVG elements for each
    drawings = {}
    for base_id, outline in outlines.items():
        drawing = svgwrite.Drawing(debug=True)
        drawing.add(Polygon([(p.x, p.y) for p in outline]))  # type: ignore
        drawings[base_id] = drawing
    # Serialise SVGs
    return {k: v.tostring() for k, v in drawings.items()}


def _connect_outlines(outlines: List[Tuple[_Point, _Point]]) -> List[_Point]:
    """Connect a set of outlines into a closed polygon.

    This mangles the input outlines list; be sure to pass a copy if you
    still need to use the original elsewhere.

    Args:
        outlines (List[Tuple[_Point, _Point]]): The outlines to connect

    Raises:
        ValueError: Raised if the outlines are disjoint or not closed

    Returns:
        List[_Point]: Closed outlines

    """
    # Remove outline ordering; these sets will only ever hold two items
    lines: List[Set[_Point]] = [set(t) for t in outlines]
    # Output polygon
    polygon: List[_Point] = []
    # Populate with first segment
    polygon.extend(lines.pop())
    # Container for currently active points (i.e. loose ends in the poly line)
    active = set(polygon)
    # Process all input lines
    while lines:
        # Find a segment that shares a point with the current endpoints
        for line in lines:
            if line.intersection(active):
                lines.remove(line)
                # If the current line and endpoints are identical, do nothing.
                # This just closes up the polygon and empties the input list.
                if not (diff := line.difference(active)):
                    break
                # Two lines should never have more than one shared point
                assert len(diff) == 1
                new_element = diff.pop()
                # "Symmetric difference update" is basically an XOR
                active.symmetric_difference_update(line)
                # Add the new point to the right end of the polygon
                if line.intersection({polygon[0]}):
                    polygon.insert(0, new_element)
                else:
                    polygon.append(new_element)
                # Break the for loop since we changed the number of elements in
                # the list; the iterator is not a fan of sizes changing.
                break
        else:
            # This is executed if no intersection was found between the active
            # endpoints and the input lines.
            raise RuntimeError(
                'Unable to close hex outline, input might be disjoint?')
    return polygon


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


def _get_hexes_outline(hexes: Iterable[_Tile], radius: float,
                       precision: float = 1e-12
                       ) -> List[Tuple[_Point, _Point]]:
    """Return the exterior edges of the given list of tiles.

    This loops over every hex in the group and checks its neighbours
    for containment in the group. If the neighbours are not part of the
    input group, the edge is considered an exterior boundary and added
    to the output list.

    Args:
        hexes (Iterable[_Tile]): The list of hexes to outline
        radius (float): The radius of the hexagons
        precision (float, optional): Rounding precision for output
            points. Defaults to 1e-12.

    Returns:
        List[Tuple[_Point, _Point]]: An unsorted list of exterior edges

    """
    # Create a cache of all hexes
    members: Set[_Tile] = set(hexes)
    # Create a list of all edges between member hexagons and those neighbours
    # that are not part of the group
    edges = [_get_hex_edge(_tile_to_point(h, radius), radius, i)
             for h in members for i, n in enumerate(_get_hex_neighbours(h))
             if n not in members]
    digits = max(-int(math.log10(precision)), 0)
    return [tuple(_Point(round(p.x, digits), round(p.y, digits)) for p in e)
            for e in edges]


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
