"""Draw perspective buildings: street wall (windows, screens, storefronts), front, roof.

Walls are filled one screen column at a time, inverting the projection to get
the world point under each pixel; windows and screens are pure functions of
that point, so they stay glued to the facade as the camera moves.
"""

from __future__ import annotations

from typing import Optional, Tuple

from animation import theme
from animation.camera import NEAR, Camera
from animation.fog import fogged
from animation.raster import Canvas
from animation.screens import WallScreen, screen_pixel
from animation.world import BACK_ROW_HEIGHT, BACK_ROW_X, PERIOD, Box

WINDOW_PITCH_U = 3.0
WINDOW_PITCH_Y = 4.0
STOREFRONT_TOP = 4.5
EMISSIVE_FOG = 0.45  # screens and shop lights cut through the fog this much better
STOREFRONT = "#7d6f4c"
MULLION = "#0b1a22"


def window_color(seed: int, u: float, y: float, height: float) -> Optional[str]:
    """Colour of the window at facade coords (u along the wall, y up), or None for wall."""
    col_frac = u % WINDOW_PITCH_U
    row_frac = y % WINDOW_PITCH_Y
    if not (1.0 <= col_frac < 2.1 and 1.3 <= row_frac < 3.1) or y < 6 or y > height - 3:
        return None
    col, row = int(u // WINDOW_PITCH_U), int(y // WINDOW_PITCH_Y)
    noise = (seed * 73856093 ^ col * 19349663 ^ row * 83492791) & 0xFFFF
    if noise % 1000 < theme.WINDOW_LIT_CHANCE * 1000:
        return theme.WINDOW_LIT[noise % len(theme.WINDOW_LIT)]
    return theme.WINDOW_UNLIT


def _paint(canvas: Canvas, x: int, y: int, color: str, depth: float) -> None:
    base, other, level = fogged(color, depth)
    canvas.fill_column(x, y, y + 1, base, other, level)


def _facade_color(seed: int, screens: Tuple[WallScreen, ...], z: float, y: float,
                  height: float, tone: str, scroll: float) -> Tuple[str, bool]:
    """(colour, emissive) of a street-facing wall at world (z, y)."""
    screen = screen_pixel(screens, z, y, scroll, phase=int(scroll * 2))
    if screen is not None:
        return screen, True
    if 0.8 < y < STOREFRONT_TOP:
        return (MULLION if (z % 2.5) < 0.35 else STOREFRONT), True
    return window_color(seed, z % PERIOD, y, height) or tone, False


def draw_side_wall(canvas: Canvas, camera: Camera, wall_x: float, span: Tuple[float, float],
                   height: float, tone: str, seed: int,
                   screens: Tuple[WallScreen, ...] = (), scroll: float = 0.0) -> None:
    """Wall in the plane x = wall_x between span = (z0, z1), seen at a grazing angle."""
    z0, z1 = max(span[0], camera.z + NEAR), span[1]
    if z1 <= z0:
        return
    sx_a, sx_b = sorted((camera.screen_x(wall_x, z0), camera.screen_x(wall_x, z1)))
    offset = wall_x - camera.x
    for x in range(max(0, int(sx_a)), min(canvas.width, int(sx_b) + 1)):
        dx = x + 0.5 - camera.screen_width / 2
        if dx == 0 or (dx > 0) != (offset > 0):
            continue
        z = camera.z + offset * camera.focal / dx
        if z0 <= z <= z1:
            _wall_column(canvas, camera, x, z, (height, tone, seed, screens, scroll))


def _wall_column(canvas: Canvas, camera: Camera, x: int, z: float, wall: tuple) -> None:
    height, tone, seed, screens, scroll = wall
    depth = z - camera.z
    top, bottom = camera.screen_y(height, z), camera.screen_y(0, z)
    for y in range(max(0, int(top + 0.5)), min(canvas.height, int(bottom + 0.5))):
        world_y = camera.y - (y + 0.5 - camera.horizon) * depth / camera.focal
        color, emissive = _facade_color(seed, screens, z, world_y, height, tone, scroll)
        _paint(canvas, x, y, color, depth * EMISSIVE_FOG if emissive else depth)


def draw_front(canvas: Canvas, camera: Camera, box: Box) -> None:
    """Face at z = z0 (towards the camera): a screen-aligned rectangle."""
    depth = box.z0 - camera.z
    if depth < NEAR:
        return
    left, top = camera.project(box.x0, box.height, box.z0)
    right, bottom = camera.project(box.x1, 0, box.z0)
    for x in range(max(0, int(left + 0.5)), min(canvas.width, int(right + 0.5))):
        world_x = camera.x + (x + 0.5 - camera.screen_width / 2) * depth / camera.focal
        for y in range(max(0, int(top + 0.5)), min(canvas.height, int(bottom + 0.5))):
            world_y = camera.y - (y + 0.5 - camera.horizon) * depth / camera.focal
            color = window_color(box.seed + 7, world_x, world_y, box.height) or theme.WALL_FRONT
            _paint(canvas, x, y, color, depth)


def draw_roof(canvas: Canvas, camera: Camera, box: Box) -> None:
    """Flat roof, visible only when the camera is above it; lit street-side edge."""
    if camera.y <= box.height:
        return
    z0 = max(box.z0, camera.z + NEAR)
    if box.z1 <= z0:
        return
    corners = [(box.x0, z0), (box.x1, z0), (box.x1, box.z1), (box.x0, box.z1)]
    points = [camera.project(x, box.height, z) for x, z in corners]
    base, other, level = fogged(theme.ROOF, (z0 + box.z1) / 2 - camera.z)
    canvas.fill_polygon(points, base, other, level)
    edge_a = camera.project(box.street_x, box.height, z0)
    edge_b = camera.project(box.street_x, box.height, box.z1)
    canvas.line(*edge_a, *edge_b, fogged(theme.ROOF_EDGE, box.z0 - camera.z)[0])


def draw_back_rows(canvas: Canvas, camera: Camera) -> None:
    """Continuous tall walls behind both rows; only seen through the alleys."""
    span = (camera.z, camera.z + theme.FOG_FAR)
    for side in (-1, 1):
        draw_side_wall(canvas, camera, side * BACK_ROW_X, span, BACK_ROW_HEIGHT,
                       theme.WALL_BACK_ROW, seed=500 + side)


def draw_box(canvas: Canvas, camera: Camera, box: Box, scroll: float) -> None:
    """Painter's order within a box: roof, street wall, front."""
    draw_roof(canvas, camera, box)
    draw_side_wall(canvas, camera, box.street_x, (box.z0, box.z1), box.height,
                   theme.WALL_SIDE, box.seed, box.screens, scroll)
    draw_front(canvas, camera, box)
