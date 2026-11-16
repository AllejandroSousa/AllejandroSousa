"""16x16 pixel-art versions of the stack logos shown on the billboards.

Hand-drawn simplifications in each project's brand colours. Shapes that are
symmetric or mathematical (Python's rotated twin, hexagon, circles) are
generated so the grids stay correct by construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from animation.pixels import Palette, PixelGrid, grid_from_cells

SIZE = 16


@dataclass(frozen=True)
class Logo:
    """A billboard logo: its grid, palette and the colour of its neon glow."""

    name: str
    grid: PixelGrid
    palette: Palette
    glow: str


def ruby() -> Logo:
    """Faceted red gem."""
    grid = [
        "................",
        "................",
        "....KKKKKKKK....",
        "...KlLLlLLlLK...",
        "..KlLLlLLlLLLK..",
        ".KKKKKKKKKKKKKK.",
        ".KRRrRRRRRRrRRK.",
        "..KRrRRRRRRrRK..",
        "...KRrRRRRrRK...",
        "....KRrRRrRK....",
        ".....KRrrRK.....",
        "......KRRK......",
        ".......KK.......",
        "................",
        "................",
        "................",
    ]
    palette = {"K": "#5c0d0a", "l": "#ff9a8f", "L": "#f0544a", "R": "#cc342d", "r": "#8f1d16"}
    return Logo("ruby", grid, palette, "#ff4d4d")


def _python_blue_cells() -> Dict[Tuple[int, int], str]:
    """Blue snake: head on top, body across the middle, tail down the left."""
    spans = {
        0: (5, 10), 1: (4, 11), 2: (4, 11), 3: (8, 11),
        4: (1, 10), 5: (0, 10), 6: (0, 10), 7: (0, 10),
        8: (0, 3), 9: (0, 3), 10: (1, 3),
    }  # fmt: skip
    cells = {(x, y): "B" for y, (lo, hi) in spans.items() for x in range(lo, hi + 1)}
    cells[(6, 1)] = "W"
    return cells


def python() -> Logo:
    """Two interlocked snakes; the yellow one is the blue one rotated 180 degrees."""
    blue = _python_blue_cells()
    yellow = {
        (SIZE - 1 - x, SIZE - 1 - y): ("Y" if key == "B" else "W") for (x, y), key in blue.items()
    }
    palette = {"B": "#3776ab", "Y": "#ffd43b", "W": "#ffffff"}
    return Logo("python", grid_from_cells(SIZE, SIZE, {**blue, **yellow}), palette, "#4b8bff")


def javascript() -> Logo:
    """Yellow square with 'JS' in the bottom-right corner."""
    letters = [
        "..#.###",
        "..#.#..",
        "..#.###",
        "#.#...#",
        ".#..###",
    ]
    cells = {(x, y): "Y" for x in range(1, 15) for y in range(1, 15)}
    for row, line in enumerate(letters):
        for col, ch in enumerate(line):
            if ch == "#":
                cells[(7 + col, 8 + row)] = "K"
    palette = {"Y": "#f7df1e", "K": "#1a1a1a"}
    return Logo("javascript", grid_from_cells(SIZE, SIZE, cells), palette, "#f7df1e")


def _hexagon_span(row: int) -> Tuple[int, int]:
    """Columns covered by a pointy-top hexagon on a 16x16 grid."""
    edge = {0: 7, 1: 5, 2: 3, 13: 3, 14: 5, 15: 7}
    lo = edge.get(row, 1)
    return lo, SIZE - 1 - lo


def _hexagon_shade(x: int, y: int) -> str:
    """Light top-left, dark bottom-right, mid elsewhere (like the official mark)."""
    if x + y < 13:
        return "L"
    return "D" if x + y > 17 else "M"


def cpp() -> Logo:
    """Blue hexagon with a white C and two plus signs."""
    cells = {}
    for y in range(SIZE):
        lo, hi = _hexagon_span(y)
        for x in range(lo, hi + 1):
            cells[(x, y)] = _hexagon_shade(x, y)
    letter_c = [(x, 4) for x in range(3, 8)] + [(x, 11) for x in range(3, 8)]
    letter_c += [(x, y) for x in (2, 3) for y in range(5, 11)]
    plus = [(9, 8), (8, 8), (10, 8), (9, 7), (9, 9), (12, 8), (11, 8), (13, 8), (12, 7), (12, 9)]
    for point in letter_c + plus:
        cells[point] = "W"
    palette = {"L": "#659ad2", "M": "#00599c", "D": "#004482", "W": "#ffffff"}
    return Logo("cpp", grid_from_cells(SIZE, SIZE, cells), palette, "#3b8eea")


def _face_cells() -> Dict[Tuple[int, int], str]:
    """Round yellow face with an orange rim, centred slightly above the middle."""
    cells = {}
    for y in range(SIZE):
        for x in range(SIZE):
            dist = ((x - 7.5) ** 2 + (y - 7.0) ** 2) ** 0.5
            if dist <= 6.2:
                cells[(x, y)] = "Y"
            elif dist <= 7.2:
                cells[(x, y)] = "O"
    return cells


def huggingface() -> Logo:
    """The hugging-face emoji: smiling face with two hands in front."""
    cells = _face_cells()
    features = {
        (5, 5): "K", (5, 6): "K", (10, 5): "K", (10, 6): "K",
        (4, 9): "K", (11, 9): "K", (5, 10): "K", (10, 10): "K",
        (6, 10): "T", (7, 10): "T", (8, 10): "T", (9, 10): "T",
        (6, 11): "K", (7, 11): "K", (8, 11): "K", (9, 11): "K",
    }  # fmt: skip
    cells.update(features)
    for x0 in (0, 11):
        for x in range(x0, x0 + 5):
            for y in range(11, 15):
                corner = (x in (x0, x0 + 4)) and (y in (11, 14))
                if not corner:
                    cells[(x, y)] = "H"
    palette = {"Y": "#ffd21e", "O": "#ff9d0b", "K": "#3a3b45", "T": "#ef4e4e", "H": "#ff9d0b"}
    return Logo("huggingface", grid_from_cells(SIZE, SIZE, cells), palette, "#ffb700")


def _shield_span(row: int) -> Tuple[int, int]:
    """Columns of a shield: straight sides, then tapering to a point."""
    if row < 9:
        return 2, 13
    inset = row - 7
    return 2 + inset, 13 - inset


def appsec() -> Logo:
    """Green shield with a padlock."""
    cells = {}
    for y in range(1, 15):
        lo, hi = _shield_span(y)
        for x in range(lo, hi + 1):
            on_rim = x in (lo, hi) or y == 1
            cells[(x, y)] = "D" if on_rim else "G"
    shackle = [(6, 3), (7, 3), (8, 3), (9, 3)] + [(x, y) for x in (5, 10) for y in (4, 5, 6)]
    body = [(x, y) for x in range(4, 12) for y in range(7, 12)]
    for point in shackle + body:
        cells[point] = "W"
    for point in [(7, 8), (8, 8), (7, 9), (8, 9), (7, 10), (8, 10)]:
        cells[point] = "D"
    palette = {"G": "#2ea043", "D": "#1a7f37", "W": "#f0fff4"}
    return Logo("appsec", grid_from_cells(SIZE, SIZE, cells), palette, "#3fb950")


def all_logos() -> List[Logo]:
    """Logos in the order the hero swings past them."""
    return [ruby(), python(), javascript(), cpp(), huggingface(), appsec()]
