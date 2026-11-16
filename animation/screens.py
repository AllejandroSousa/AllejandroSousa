"""Times Square style screens, flush on the street-facing walls.

Six big logo billboards (one per stack) plus code/glyph screens filling the
facades. Many have a marquee border of bulbs. Screens are emissive: they are
fogged less than walls, so they glow through the rain.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from animation import theme
from animation.logos import Logo

INKS = ("#3f8f9c", "#b08a45", "#4c9a70", "#8d5a86", "#6d8fc2", "#a5524f")
BULB_ON, BULB_FRAME = "#d6c48c", "#16120c"
BULB_BORDER = 0.6  # world units of marquee around a screen
CODE_ROW = 1.0  # world units per code line
CODE_PATTERN_ROWS = 24  # code repeats every this many rows, so scrolling can loop
GLYPHS: Dict[str, Tuple[str, ...]] = {
    "</>": ("..#...#.#...", ".#...#...#..", "#...#.....#.", ".#.#.....#..", "..##....#..."),
    "{ }": (".##.....##.", ".#.......#.", "#.........#", ".#.......#.", ".##.....##."),
    ">_": ("#.....", ".#....", "..#...", ".#....", "#.####"),
    "01": (".#...#.", "#.#.##.", "#.#..#.", "#.#..#.", ".#..###"),
}


@dataclass(frozen=True)
class WallScreen:
    """Screen on a street-facing wall spanning z0..z1 and y0..y1.

    `kind` is "code", "logo" or a key of GLYPHS. `mirrored` is True on the right
    side of the avenue, where facade-left is towards smaller z.
    """

    z0: float
    z1: float
    y0: float
    y1: float
    kind: str
    ink: str
    seed: int
    mirrored: bool = False
    bulbs: bool = False
    logo: Optional[Logo] = None

    def shifted(self, dz: float) -> "WallScreen":
        return WallScreen(self.z0 + dz, self.z1 + dz, self.y0, self.y1, self.kind, self.ink,
                          self.seed, self.mirrored, self.bulbs, self.logo)


def wall_screens_for(z0: float, z1: float, height: float, mirrored: bool,
                     rng: random.Random) -> List[WallScreen]:
    """1-3 big screens stacked on one facade (Times Square density)."""
    screens = []
    y = rng.uniform(5, 8)
    for _ in range(rng.choice((1, 2, 2, 3))):
        tall = rng.uniform(9, 20)
        margin = rng.uniform(0.8, 2.5)
        if y + tall > height - 4 or z1 - z0 < 2 * margin + 6:
            break
        kind = rng.choice(("code", "code", "code") + tuple(GLYPHS))
        screens.append(WallScreen(z0 + margin, z1 - margin, y, y + tall, kind, rng.choice(INKS),
                                  rng.randint(0, 10**6), mirrored, rng.random() < 0.5))
        y += tall + rng.uniform(1.5, 5)
    return screens


def logo_billboard(z0: float, z1: float, logo: Logo, mirrored: bool) -> WallScreen:
    """Square logo billboard with a bulb marquee, low on the facade so it reads."""
    side = min(z1 - z0 - 3, 20.0)
    start = (z0 + z1 - side) / 2
    return WallScreen(start, start + side, 6.0, 6.0 + side, "logo", logo.glow, 0, mirrored, True, logo)


def _code_texel(screen: WallScreen, u_world: float, v_world: float, scroll: float) -> Optional[str]:
    """Lines of 'code': indented dashes of varying length, scrolling upward."""
    row = int((v_world + scroll) // CODE_ROW) % CODE_PATTERN_ROWS
    if (v_world + scroll) % CODE_ROW < CODE_ROW * 0.45:
        return None
    noise = (screen.seed * 2654435761 ^ row * 40503) & 0xFFFFF
    indent = (noise % 4) * 0.9
    length = 2.0 + (noise >> 4) % 9
    if indent + 0.4 <= u_world < indent + 0.4 + length + 4 and (noise >> 9) % 7:
        return screen.ink
    return None


def _glyph_texel(screen: WallScreen, u: float, v: float) -> Optional[str]:
    """One big glyph centred on the screen (u, v in 0..1)."""
    rows = GLYPHS[screen.kind]
    cols = len(rows[0])
    gx, gy = int((u - 0.1) / 0.8 * cols), int((v - 0.15) / 0.7 * len(rows))
    if 0 <= gx < cols and 0 <= gy < len(rows) and rows[gy][gx] == "#":
        return screen.ink
    return None


def _logo_texel(screen: WallScreen, u: float, v: float) -> str:
    """Logo on a dark brand-tinted background, with a thin margin."""
    logo = screen.logo
    size = len(logo.grid)
    margin = 0.1
    gx = int((u - margin) / (1 - 2 * margin) * size)
    gy = int((v - margin) / (1 - 2 * margin) * size)
    if 0 <= gx < size and 0 <= gy < size and logo.grid[gy][gx] != ".":
        return theme.mix(logo.palette[logo.grid[gy][gx]], theme.FOG, 0.15)
    return theme.mix(logo.glow, "#000000", 0.82)


def wall_screen_color(screen: WallScreen, z: float, y: float, scroll: float) -> str:
    """Colour of a screen's face at world (z, y); `scroll` animates the code."""
    along = screen.z1 - z if screen.mirrored else z - screen.z0
    u_world, v_world = along, screen.y1 - y
    u, v = u_world / (screen.z1 - screen.z0), v_world / (screen.y1 - screen.y0)
    if screen.kind == "logo":
        return _logo_texel(screen, u, v)
    ink = _code_texel(screen, u_world, v_world, scroll) if screen.kind == "code" else _glyph_texel(screen, u, v)
    return ink or theme.mix(screen.ink, "#000000", 0.8)


def bulb_color(z: float, y: float, phase: int) -> str:
    """Marquee: small bulbs every 1.2 units on a dark frame, chasing as `phase` advances."""
    index = int(z / 1.2) + int(y / 1.2)
    on_bulb = (z % 1.2) < 0.45 and (y % 1.2) < 0.45
    return BULB_ON if on_bulb and (index + phase) % 2 == 0 else BULB_FRAME


def screen_pixel(screens: Tuple[WallScreen, ...], z: float, y: float, scroll: float,
                 phase: int) -> Optional[str]:
    """Colour of a screen face or its bulb border at (z, y), or None if bare wall."""
    for screen in screens:
        if screen.z0 <= z < screen.z1 and screen.y0 <= y < screen.y1:
            return wall_screen_color(screen, z, y, scroll)
        if screen.bulbs and (screen.z0 - BULB_BORDER <= z < screen.z1 + BULB_BORDER
                             and screen.y0 - BULB_BORDER <= y < screen.y1 + BULB_BORDER):
            return bulb_color(z, y, phase)
    return None
