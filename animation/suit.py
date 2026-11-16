"""Suit pattern in the style of the 2002 film suit (Raimi).

Back: navy with a large red spider in the middle; red web-lined yoke over the
shoulders whose lower edge dips at the centre; red web-lined belt. Arms red with
a navy stripe on the inner upper arm; legs navy with red boots to mid-shin;
red gloves. Front: red chest with a small black spider. Mask: red with a
lat/long web and white lenses rimmed in black.

Patterns use the hit position along the spine (pelvis -> neck), so the many
overlapping spheres of the torso agree on one continuous drawing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from animation.hero_poses import Skeleton, Vec3
from animation.raster import RGB, hex_to_rgb

RED, NAVY = hex_to_rgb("#b3262e"), hex_to_rgb("#1b2a55")
BODY_WEB, MASK_WEB = hex_to_rgb("#5c121b"), hex_to_rgb("#2a0b10")
EYE, EYE_EDGE, CHEST_SPIDER = hex_to_rgb("#e8f0f4"), hex_to_rgb("#050608"), hex_to_rgb("#08080d")
UNSHADED = (EYE, EYE_EDGE, CHEST_SPIDER)
MASK_WEB_SPACING = 0.42
LINE = 0.9  # web line width, in pixels
BELT = (0.06, 0.12)  # metres above the pelvis joint, along the spine

# Back spider legs as polylines (x, s) in metres from the emblem centre; mirrored in x.
SPIDER_LEGS: Tuple[Tuple[Tuple[float, float], ...], ...] = (
    ((0.03, 0.04), (0.10, 0.08), (0.12, 0.17)),
    ((0.03, 0.02), (0.12, 0.04), (0.17, 0.10)),
    ((0.03, -0.02), (0.12, -0.04), (0.17, -0.11)),
    ((0.03, -0.04), (0.10, -0.08), (0.12, -0.17)),
)


@dataclass(frozen=True)
class SurfaceHit:
    """What the suit needs to know about one pixel of the body."""

    material: str
    side: int  # -1 left limb, +1 right limb, 0 centre
    along: float  # 0..1 along the limb
    limb_len: float
    normal: Vec3  # hero-local
    point: Vec3  # hero-local
    pixel_size: float  # world metres per pixel at this hit
    radius_px: float


def _segment_distance(p: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    u = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - ax - u * dx, p[1] - ay - u * dy)


def _on_polyline(p: Tuple[float, float], points: Sequence[Tuple[float, float]], width: float) -> bool:
    return any(_segment_distance(p, a, b) < width for a, b in zip(points, points[1:]))


def back_spider(x: float, s: float, pixel: float) -> bool:
    """Large spider: oval body, small head, four bent legs per side."""
    if (x / 0.046) ** 2 + (s / 0.088) ** 2 < 1 or (x / 0.03) ** 2 + ((s - 0.1) / 0.032) ** 2 < 1:
        return True
    width = max(0.011, pixel * 0.7)
    return any(_on_polyline((abs(x), s), leg, width) for leg in SPIDER_LEGS)


def _spine_coords(point: Vec3, pose: Skeleton) -> Tuple[float, float, float]:
    """(lateral x, metres along spine from pelvis, spine length)."""
    px, py, pz = pose["pelvis"]
    nx, ny, nz = pose["neck"]
    ax, ay, az = nx - px, ny - py, nz - pz
    length = math.sqrt(ax * ax + ay * ay + az * az)
    t = ((point[0] - px) * ax + (point[1] - py) * ay + (point[2] - pz) * az) / (length * length)
    return point[0] - (px + t * ax), t * length, length


def _radial_web(x: float, y: float, pixel: float, spacing: float = 0.1) -> bool:
    """Spokes and rings around (0, 0), ~1px wide; hidden when too dense to read."""
    if spacing / pixel < 4:
        return False
    r = math.hypot(x, y)
    if r < 0.05:
        return False
    spoke = (math.atan2(y, x) % (math.pi / 6)) * r < pixel * LINE
    return spoke or r % spacing < pixel * LINE


def _red_with_web(web: bool) -> RGB:
    return BODY_WEB if web else RED


def torso_color(hit: SurfaceHit, pose: Skeleton) -> RGB:
    """Back: navy, red yoke and belt, big red spider. Front: red chest, black spider."""
    x, s, length = _spine_coords(hit.point, pose)
    emblem_s = length * 0.52
    if hit.normal[2] > 0.35:  # chest, facing away from the camera
        if (x / 0.03) ** 2 + ((s - emblem_s) / 0.06) ** 2 < 1:
            return CHEST_SPIDER
        return _red_with_web(_radial_web(x, s - emblem_s, hit.pixel_size)) if abs(x) < 0.14 else NAVY
    if BELT[0] < s < BELT[1]:
        return _red_with_web((s - BELT[0]) % 0.03 < hit.pixel_size * LINE)
    if s <= BELT[0]:
        return NAVY  # hips below the belt
    yoke_edge = length * 0.74 + 0.6 * abs(x)
    if s > min(yoke_edge, length * 0.9):
        return _red_with_web(_radial_web(x, s - emblem_s, hit.pixel_size))
    if hit.normal[2] < -0.3 and back_spider(x, s - emblem_s, hit.pixel_size):
        return RED
    return NAVY


def _limb_web(hit: SurfaceHit, spacing: float = 0.09) -> bool:
    """Rings along the limb plus lines down its length."""
    if spacing / hit.pixel_size < 4:
        return False
    nx, _, nz = hit.normal
    ring = (hit.along * hit.limb_len) % spacing < hit.pixel_size * LINE
    radius = hit.pixel_size * hit.radius_px
    seam = (math.atan2(nx, nz) % 0.7) * radius < hit.pixel_size * LINE
    return ring or seam


def limb_color(hit: SurfaceHit) -> RGB:
    """Arms red (navy inner upper arm), legs navy, boots/gloves red, all red parts webbed."""
    material = hit.material
    if material == "thigh" or (material == "shin" and hit.along < 0.45):
        return NAVY
    if material == "upper_arm" and hit.normal[0] * hit.side < -0.35 and hit.normal[1] < 0.3:
        return NAVY
    if material in ("glove", "boot", "shoulder"):
        return _red_with_web(mask_web(hit.normal, hit.radius_px))
    return _red_with_web(_limb_web(hit))


def mask_web(normal: Vec3, radius_px: float) -> bool:
    """Latitude/longitude grid on a single sphere, ~1px wide; off when too small."""
    if radius_px < 4.5:
        return False
    nx, ny, nz = normal
    width = LINE / radius_px
    theta, phi = math.atan2(nx, nz), math.asin(max(-1.0, min(1.0, ny)))
    return (theta % MASK_WEB_SPACING) < width or (phi % MASK_WEB_SPACING) < width


def eye(normal: Vec3) -> Optional[RGB]:
    """Teardrop lenses on the front-sides of the mask, with a black rim."""
    nx, ny, nz = normal
    ax = abs(nx)
    top = 0.44 - 0.55 * max(0.0, ax - 0.2)
    if nz < 0.15:
        return None
    if 0.2 < ax < 0.74 and -0.06 < ny < top:
        return EYE
    if 0.15 < ax < 0.8 and -0.12 < ny < top + 0.07:
        return EYE_EDGE
    return None


def _turn(normal: Vec3, pose: Skeleton) -> Vec3:
    """Normal in the mask's own frame: undo the head's yaw towards the gaze point."""
    hx, _, hz = pose["head"]
    gx, _, gz = pose["gaze"]
    yaw = math.atan2(gx - hx, gz - hz)
    nx, ny, nz = normal
    c, s = math.cos(yaw), math.sin(yaw)
    return (nx * c - nz * s, ny, nx * s + nz * c)


def suit_color(hit: SurfaceHit, pose: Skeleton) -> RGB:
    """Base colour of the suit at one pixel, before lighting."""
    if hit.material == "head":
        mask_n = _turn(hit.normal, pose)
        return eye(mask_n) or (MASK_WEB if mask_web(mask_n, hit.radius_px) else RED)
    if hit.material == "torso":
        return torso_color(hit, pose)
    return limb_color(hit)
