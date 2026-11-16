"""Tiny software rasterizer for pixel-art frames (no anti-aliasing, by design).

Colours are (r, g, b) tuples. Fills accept a second colour and a 0..1 level to
blend the two with a 4x4 Bayer ordered dither, the classic pixel-art way to fake
gradients (fog, sky) with flat colours.
"""

from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple


RGB = Tuple[int, int, int]

BAYER_4 = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


def hex_to_rgb(color: str) -> RGB:
    """'#a1b2c3' -> (161, 178, 195).

    >>> hex_to_rgb("#ff0080")
    (255, 0, 128)
    """
    if len(color) != 7 or not color.startswith("#"):
        raise ValueError(f"expected colour like '#a1b2c3', got {color!r}")
    return tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]


def dither_pick(x: int, y: int, base: RGB, other: Optional[RGB], level: float) -> RGB:
    """Choose `other` on a fraction `level` of pixels, spread by the Bayer matrix."""
    if other is None or level <= 0:
        return base
    return other if (BAYER_4[y % 4][x % 4] + 0.5) / 16 < level else base


class Canvas:
    """A width x height grid of RGB pixels."""

    def __init__(self, width: int, height: int, fill: RGB) -> None:
        self.width = width
        self.height = height
        self.pixels: List[List[RGB]] = [[fill] * width for _ in range(height)]

    def put(self, x: int, y: int, color: RGB) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = color

    def fill_column(self, x: int, top: float, bottom: float, color: RGB,
                    other: Optional[RGB] = None, level: float = 0.0) -> None:
        """Fill pixel column x between two (fractional) y values, dithered."""
        if not 0 <= x < self.width:
            return
        y0 = max(0, int(math.ceil(top - 0.5)))
        y1 = min(self.height, int(math.ceil(bottom - 0.5)))
        row_pixels = self.pixels
        for y in range(y0, y1):
            row_pixels[y][x] = dither_pick(x, y, color, other, level)

    def fill_rect(self, x0: float, y0: float, x1: float, y1: float, color: RGB,
                  other: Optional[RGB] = None, level: float = 0.0) -> None:
        """Axis-aligned rectangle covering pixel centres inside [x0, x1) x [y0, y1)."""
        for x in range(max(0, int(math.ceil(x0 - 0.5))), min(self.width, int(math.ceil(x1 - 0.5)))):
            self.fill_column(x, y0, y1, color, other, level)

    def dither_overlay(self, x0: float, y0: float, x1: float, y1: float, color: RGB, level: float) -> None:
        """Paint `color` over a `level` fraction of the rectangle's pixels, keeping the rest."""
        for y in range(max(0, int(math.ceil(y0 - 0.5))), min(self.height, int(math.ceil(y1 - 0.5)))):
            for x in range(max(0, int(math.ceil(x0 - 0.5))), min(self.width, int(math.ceil(x1 - 0.5)))):
                if (BAYER_4[y % 4][x % 4] + 0.5) / 16 < level:
                    self.pixels[y][x] = color

    def fill_polygon(self, points: Sequence[Tuple[float, float]], color: RGB,
                     other: Optional[RGB] = None, level: float = 0.0) -> None:
        """Even-odd scanline fill sampling pixel centres."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        y0 = max(0, int(math.ceil(min(ys) - 0.5)))
        y1 = min(self.height, int(math.ceil(max(ys) - 0.5)))
        for y in range(y0, y1):
            for x0, x1 in _scanline_spans(points, y + 0.5):
                for x in range(max(0, int(math.ceil(x0 - 0.5))), min(self.width, int(math.ceil(x1 - 0.5)))):
                    self.pixels[y][x] = dither_pick(x, y, color, other, level)

    def line(self, x0: float, y0: float, x1: float, y1: float, color: RGB) -> None:
        """1px line (DDA), endpoints included."""
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            u = i / steps
            self.put(int(round(x0 + (x1 - x0) * u)), int(round(y0 + (y1 - y0) * u)), color)

    def to_rows(self) -> List[bytes]:
        """Raw RGB bytes per row (for the PNG encoder)."""
        return [bytes(channel for pixel in row for channel in pixel) for row in self.pixels]


def _scanline_spans(points: Sequence[Tuple[float, float]], y: float) -> List[Tuple[float, float]]:
    """X intervals where the horizontal line at y is inside the polygon."""
    crossings = []
    for (ax, ay), (bx, by) in zip(points, list(points[1:]) + [points[0]]):
        if (ay <= y < by) or (by <= y < ay):
            crossings.append(ax + (y - ay) * (bx - ax) / (by - ay))
    crossings.sort()
    return list(zip(crossings[::2], crossings[1::2]))
