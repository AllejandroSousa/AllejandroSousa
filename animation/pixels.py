"""Pixel-art grids: a list of equal-length strings, one palette key per character.

"." means transparent. Used for the 16x16 stack logos shown on the billboards.
"""

from __future__ import annotations

from typing import Dict, List

PixelGrid = List[str]
Palette = Dict[str, str]

TRANSPARENT = "."


def validate_grid(grid: PixelGrid, palette: Palette, name: str) -> None:
    """Raise ValueError if rows differ in width or use keys missing from the palette.

    >>> validate_grid(["R."], {"R": "#f00"}, "dot")
    """
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        raise ValueError(f"grid '{name}' has rows of widths {sorted(widths)}; expected one width")
    unknown = {ch for row in grid for ch in row} - set(palette) - {TRANSPARENT}
    if unknown:
        raise ValueError(f"grid '{name}' uses keys {sorted(unknown)} not in palette {sorted(palette)}")


def grid_from_cells(width: int, height: int, cells: Dict[tuple, str]) -> PixelGrid:
    """Build a grid from a {(x, y): key} map; unset cells are transparent.

    >>> grid_from_cells(2, 1, {(1, 0): "R"})
    ['.R']
    """
    return [
        "".join(cells.get((col, row), TRANSPARENT) for col in range(width)) for row in range(height)
    ]
