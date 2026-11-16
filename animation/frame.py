"""Render one third-person frame: backdrop, avenue, web line, 3D hero."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from animation import backdrop, buildings3d, theme
from animation.camera import Camera
from animation.hero3d import Placement, draw_hero3d, world_point
from animation.hero_poses import Skeleton, Vec3
from animation.raster import Canvas, hex_to_rgb
from animation.world import Box, visible_boxes

FRAME_WIDTH = 240
FRAME_HEIGHT = 100


@dataclass(frozen=True)
class HeroView:
    """Posed hero; `web_hand` names the joint holding the web, if swinging."""

    pose: Skeleton
    placement: Placement
    web_anchor: Optional[Vec3] = None
    web_hand: str = "r_hand"


def draw_web(canvas: Canvas, camera: Camera, hero: HeroView) -> None:
    """1px web line from the gripping hand up to the anchor."""
    if hero.web_anchor is None:
        return
    hand = camera.project(*world_point(hero.placement, hero.pose[hero.web_hand]))
    anchor = camera.project(*hero.web_anchor)
    if hand is not None and anchor is not None:
        canvas.line(hand[0], hand[1], anchor[0], anchor[1], hex_to_rgb(theme.WEB))


def render_frame(camera: Camera, city: List[Box], hero: Optional[HeroView], scroll: float = 0.0) -> Canvas:
    """Full frame, painted back to front; `scroll` animates the code screens."""
    canvas = Canvas(FRAME_WIDTH, FRAME_HEIGHT, hex_to_rgb(theme.SKY_TOP))
    backdrop.draw_sky(canvas, camera)
    backdrop.draw_far_skyline(canvas, camera)
    backdrop.draw_ground(canvas, camera)
    buildings3d.draw_back_rows(canvas, camera)
    for box in visible_boxes(city, camera.z, theme.FOG_FAR):
        buildings3d.draw_box(canvas, camera, box, scroll)
    if hero is not None:
        draw_web(canvas, camera, hero)
        draw_hero3d(canvas, camera, hero.pose, hero.placement)
    return canvas
