"""Rain streaks and a faint lightning flash.

Each rain layer is a set of streaks drawn twice, one screen-height apart, and
translated down by exactly that height per cycle, so the fall loops seamlessly.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from animation import theme


@dataclass(frozen=True)
class RainLayer:
    """One depth of rain: more distant layers are fainter, shorter and slower."""

    name: str
    seed: int
    drops: int
    length: tuple
    opacity: float
    seconds: float


BACK_RAIN = RainLayer("rain-back", 21, 70, (2, 4), 0.22, 0.9)
FRONT_RAIN = RainLayer("rain-front", 22, 40, (4, 7), 0.38, 0.55)


def render_rain(layer: RainLayer, width: int, height: int) -> str:
    """Group of vertical streaks covering two screen heights, animated by CSS."""
    rng = random.Random(layer.seed)
    streaks = []
    for _ in range(layer.drops):
        x, y = rng.randint(0, width - 1), rng.randint(0, height - 1)
        length = rng.randint(*layer.length)
        streaks.append(f"M{x} {y}h1v{length}h-1zM{x} {y + height}h1v{length}h-1z")
    return (
        f'<g class="a {layer.name}" opacity="{layer.opacity}">'
        f'<path fill="{theme.RAIN}" d="{"".join(streaks)}"/></g>'
    )


def rain_css(layer: RainLayer, height: int) -> str:
    """Seamless fall: translate from one screen-height up to rest."""
    return (
        f".{layer.name}{{animation:{layer.name} {layer.seconds}s linear infinite}}"
        f"@keyframes {layer.name}{{from{{transform:translateY(-{height}px)}}"
        f"to{{transform:translateY(0)}}}}"
    )


def render_flash(width: int, height: int) -> str:
    """Full-screen pale overlay, invisible except for a double flicker."""
    return f'<rect class="flash" width="{width}" height="{height}" fill="#cfe3ee" opacity="0"/>'


def flash_css(loop_seconds: float) -> str:
    """Double flicker around 62% of the loop, while the hero is mid-swing."""
    return (
        f".flash{{animation:flash {loop_seconds}s linear infinite}}"
        "@keyframes flash{0%,61.5%{opacity:0}62%{opacity:.09}62.6%{opacity:0}"
        "63.2%{opacity:.06}64.5%,100%{opacity:0}}"
    )
