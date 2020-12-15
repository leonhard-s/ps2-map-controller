"""Unit tests for trying to fix the map tile generator."""

import math
import unittest
from typing import Any, Tuple

from apl_backend._hexgen import (  # pylint: disable=import-error
    _Point as Point,
    _Tile as Tile,
    _get_hex_corner as get_hex_corner,
    _radius_to_size as radius_to_size,
    _tile_to_point as tile_to_point
)


class HexGenTest(unittest.TestCase):
    """Coordinate conversions and other shenanigans."""

    def _good_enuf(self, tuple_a: Tuple[Any, ...],
                   tuple_b: Tuple[Any, ...]) -> None:
        """Helper function for testing tuples with some fuzziness.

        "Fuzziness" being floating point errors due to trigonometry.
        """
        self.assertEqual(len(tuple_a), len(tuple_b), 'tuple size mismatch')
        for pos_a, pos_b in zip(tuple_a, tuple_b):
            self.assertAlmostEqual(pos_a, pos_b)

    def test_corners(self) -> None:
        """Test the hexagon corner position conversion."""
        origin = Point(0, 0)
        radius = 10
        tuple_a = get_hex_corner(origin, radius, 0)
        tuple_b = Point(5*math.sqrt(3), 5)
        self._good_enuf(tuple_a, tuple_b)

    def test_radius_to_size(self) -> None:
        """Test conversion to Cartesian sizes from hex radii."""
        width, height = radius_to_size(5.0)
        self.assertAlmostEqual(math.sqrt(3)*5.0, width)
        self.assertAlmostEqual(10.0, height)

    def test_tile_to_point(self) -> None:
        """Test the tile to point coordinate transfer."""
        tile = Tile(0, 0)
        point = tile_to_point(tile, 1.0)
        self._good_enuf(point, (0.0, 0.0))
        tile = Tile(1, 0)
        point = tile_to_point(tile, 1.0)
        self._good_enuf(point, (math.sqrt(3), 0.0))
        tile = Tile(0, 1)
        point = tile_to_point(tile, 1.0)
        self._good_enuf(point, (math.sqrt(3)*0.5, 1.5))
        tile = Tile(1, 1)
        point = tile_to_point(tile, 1.0)
        self._good_enuf(point, (math.sqrt(3)*1.5, 1.5))
