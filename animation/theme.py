"""Noir colour theme: near-monochrome petrol blue, pale window light, rain.

Everything except the hero's suit and the screens sits in this palette, so the
red suit and the emissive screens are the only strong accents.
"""

from __future__ import annotations

from typing import Tuple

SKY_TOP = "#03090d"
FOG = "#0c2230"
HORIZON_FOG = "#143545"
FOG_FAR = 260.0  # world units at which everything has melted into HORIZON_FOG
FOG_STEPS = 6  # flat fog bands, joined by ordered dithering

FAR_LIT = "#6d8a86"
WINDOW_UNLIT = "#050f15"
WINDOW_LIT = ("#e6e1bd", "#c9cfb4", "#8fa8a2")
WINDOW_LIT_CHANCE = 0.13

WALL_SIDE = "#0a1c26"
WALL_FRONT = "#06121a"
WALL_BACK_ROW = "#0c2230"
ROOF = "#0f2633"
ROOF_EDGE = "#1f4a5c"
STREET = "#071219"
SIDEWALK_TONE = "#0d202a"
LANE = "#5d7a80"

RAIN = "#7fb2cc"
WEB = "#c9d8e2"


def _rgb(color: str) -> Tuple[int, int, int]:
    """'#rrggbb' -> (r, g, b) ints."""
    if len(color) != 7 or not color.startswith("#"):
        raise ValueError(f"expected colour like '#a1b2c3', got {color!r}")
    return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))


def mix(color: str, toward: str, amount: float) -> str:
    """Blend `color` toward `toward` by `amount` (0 keeps it, 1 replaces it).

    >>> mix("#000000", "#ffffff", 0.5)
    '#808080'
    """
    a, b = _rgb(color), _rgb(toward)
    return "#" + "".join(f"{round(x + (y - x) * amount):02x}" for x, y in zip(a, b))
