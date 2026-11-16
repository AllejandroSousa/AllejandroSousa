"""Depth fog quantised into a few flat bands joined by ordered dithering."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional, Tuple

from animation import theme
from animation.raster import RGB, hex_to_rgb

FogShade = Tuple[RGB, Optional[RGB], float]


def _mix_rgb(a: RGB, b: RGB, amount: float) -> RGB:
    return tuple(round(x + (y - x) * amount) for x, y in zip(a, b))  # type: ignore[return-value]


def fog_amount(depth: float) -> float:
    """0 near the camera, 1 at FOG_FAR; eased so mid-distance still reads."""
    u = min(1.0, max(0.0, (depth - 8.0) / (theme.FOG_FAR - 8.0)))
    return u**0.75


@lru_cache(maxsize=4096)
def _band(color: str, index: int) -> RGB:
    return _mix_rgb(hex_to_rgb(color), hex_to_rgb(theme.HORIZON_FOG), index / theme.FOG_STEPS)


def fogged(color: str, depth: float) -> FogShade:
    """(base, other, level) for Canvas fills: two adjacent fog bands and the dither mix.

    >>> fogged("#000000", 0.0)[2]
    0.0
    """
    scaled = fog_amount(depth) * theme.FOG_STEPS
    index = min(theme.FOG_STEPS - 1, int(scaled))
    return _band(color, index), _band(color, index + 1), scaled - index
