"""Sky, distant skyline at the horizon, and the avenue's ground plane."""

from __future__ import annotations

import random

from animation import theme
from animation.camera import Camera
from animation.fog import fogged
from animation.raster import Canvas, hex_to_rgb
from animation.world import HALF_STREET, PERIOD, SIDEWALK

LANE_DASH = 10.0


def draw_sky(canvas: Canvas, camera: Camera) -> None:
    """Dithered vertical gradient from the night sky down to the horizon fog."""
    top, bottom = hex_to_rgb(theme.SKY_TOP), hex_to_rgb(theme.HORIZON_FOG)
    steps = 7
    bands = [tuple(round(a + (b - a) * i / steps) for a, b in zip(top, bottom)) for i in range(steps + 1)]
    for y in range(min(canvas.height, int(camera.horizon) + 1)):
        scaled = (y / max(1.0, camera.horizon)) ** 1.6 * steps
        index = min(steps - 1, int(scaled))
        for x in range(canvas.width):
            canvas.fill_column(x, y, y + 1, bands[index], bands[index + 1], scaled - index)


def draw_far_skyline(canvas: Canvas, camera: Camera) -> None:
    """Static silhouettes on the horizon (too far away for parallax)."""
    rng = random.Random(4)
    color = hex_to_rgb(theme.mix(theme.HORIZON_FOG, theme.SKY_TOP, 0.35))
    lit = hex_to_rgb(theme.mix(theme.FAR_LIT, theme.HORIZON_FOG, 0.4))
    x = 0
    while x < canvas.width:
        width, height = rng.randint(3, 9), rng.randint(3, 16)
        top = camera.horizon - height
        for column in range(x, min(canvas.width, x + width)):
            canvas.fill_column(column, top, camera.horizon + 1, color)
            if rng.random() < 0.12:
                canvas.put(column, int(top) + rng.randint(2, max(2, height - 1)), lit)
        x += width + rng.randint(0, 1)


def _ground_color(world_x: float, world_z: float) -> str:
    """Asphalt, sidewalks, and the dashed centre line."""
    if abs(world_x) > HALF_STREET - SIDEWALK:
        return theme.SIDEWALK_TONE
    if abs(world_x) < 0.35 and (world_z % LANE_DASH) < LANE_DASH / 2:
        return theme.LANE
    return theme.STREET


def draw_ground(canvas: Canvas, camera: Camera) -> None:
    """Street plane y=0: per-pixel inverse projection (cheap at this resolution)."""
    first_row = int(camera.horizon) + 1
    for y in range(first_row, canvas.height):
        depth = camera.focal * camera.y / (y + 0.5 - camera.horizon)
        world_z = (camera.z + depth) % PERIOD
        for x in range(canvas.width):
            world_x = camera.x + (x + 0.5 - camera.screen_width / 2) * depth / camera.focal
            base, other, level = fogged(_ground_color(world_x, world_z), depth)
            canvas.fill_column(x, y, y + 1, base, other, level)
