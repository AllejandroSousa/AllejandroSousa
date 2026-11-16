"""3D hero rendered as pixel art: limbs are chains of spheres ray-cast per pixel.

Each pixel keeps the nearest sphere hit (z-buffer), then gets the suit colour
(see `suit`), cel shading in three tones, a cold rim light from the city ahead,
and the figure gets a 1px dark outline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from animation.camera import NEAR, Camera
from animation.hero_poses import Skeleton, Vec3
from animation.raster import RGB, Canvas, hex_to_rgb
from animation.suit import UNSHADED, SurfaceHit, suit_color

OUTLINE, RIM = hex_to_rgb("#03060a"), hex_to_rgb("#7fb2cc")
TONES = (0.42, 0.7, 1.0)
KEY_LIGHT = (0.35, 0.55, -0.76)
RIM_LIGHT = (-0.15, 0.25, 0.96)

# (joint a, joint b, radius at a, radius at b, material, side)
LIMBS = (
    ("neck", "chest", 0.08, 0.2, "torso", 0), ("chest", "pelvis", 0.2, 0.15, "torso", 0),
    ("l_sho", "l_elb", 0.088, 0.07, "upper_arm", -1), ("l_elb", "l_hand", 0.07, 0.055, "forearm", -1),
    ("r_sho", "r_elb", 0.088, 0.07, "upper_arm", 1), ("r_elb", "r_hand", 0.07, 0.055, "forearm", 1),
    ("l_hip", "l_knee", 0.115, 0.085, "thigh", -1), ("l_knee", "l_foot", 0.085, 0.06, "shin", -1),
    ("r_hip", "r_knee", 0.115, 0.085, "thigh", 1), ("r_knee", "r_foot", 0.085, 0.06, "shin", 1),
)  # fmt: skip
BALLS = (
    ("head", 0.135, "head", 0), ("l_sho", 0.1, "shoulder", -1), ("r_sho", 0.1, "shoulder", 1),
    ("l_hand", 0.065, "glove", -1), ("r_hand", 0.065, "glove", 1), ("l_hip", 0.11, "thigh", -1),
    ("r_hip", 0.11, "thigh", 1), ("l_foot", 0.07, "boot", -1), ("r_foot", 0.07, "boot", 1),
)  # fmt: skip
LATS = 0.11  # x offset of the two extra chest spheres that broaden the back


@dataclass(frozen=True)
class Placement:
    """Where the skeleton's origin is in the world, plus body rotation in degrees.

    pitch leans forward (around x), yaw turns the body (around y, positive turns
    the hero's front towards +x), roll leans sideways (around z).
    """

    position: Vec3
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0


@dataclass(frozen=True)
class Sphere:
    center: Vec3
    radius: float
    material: str
    side: int = 0
    along: float = 0.0  # 0..1 position along its limb
    limb_len: float = 0.0  # metres


@dataclass
class Hit:
    depth: float
    sphere: Sphere
    normal: Vec3  # hero-local
    radius_px: float
    point: Vec3  # hero-local


def _rotate(v: Vec3, roll: float, pitch: float, yaw: float = 0.0) -> Vec3:
    """Pitch around x, then yaw around y, then roll around z."""
    x, y, z = v
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    y, z = y * cp - z * sp, y * sp + z * cp
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    x, z = x * cy + z * sy, -x * sy + z * cy
    cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
    return (x * cr - y * sr, x * sr + y * cr, z)


def _unrotate(v: Vec3, roll: float, pitch: float, yaw: float = 0.0) -> Vec3:
    """Inverse of `_rotate`."""
    x, y, z = v
    cr, sr = math.cos(math.radians(-roll)), math.sin(math.radians(-roll))
    x, y = x * cr - y * sr, x * sr + y * cr
    cy, sy = math.cos(math.radians(-yaw)), math.sin(math.radians(-yaw))
    x, z = x * cy + z * sy, -x * sy + z * cy
    cp, sp = math.cos(math.radians(-pitch)), math.sin(math.radians(-pitch))
    return (x, y * cp - z * sp, y * sp + z * cp)


def world_point(placement: Placement, local: Vec3) -> Vec3:
    """Hero-local point -> world."""
    rx, ry, rz = _rotate(local, placement.roll, placement.pitch, placement.yaw)
    px, py, pz = placement.position
    return (px + rx, py + ry, pz + rz)


def body_spheres(pose: Skeleton) -> List[Sphere]:
    """Sphere-sweep every limb with spheres overlapping by ~40% of their radius."""
    spheres = [Sphere(pose[j], r, m, side) for j, r, m, side in BALLS]
    cx, cy, cz = pose["chest"]
    spheres += [Sphere((cx + side * LATS, cy + 0.02, cz), 0.15, "torso", 0, 0.5) for side in (-1, 1)]
    for a, b, ra, rb, material, side in LIMBS:
        length = math.dist(pose[a], pose[b])
        steps = max(2, int(length / (min(ra, rb) * 0.6)))
        for i in range(steps + 1):
            u = i / steps
            center = tuple(pa + (pb - pa) * u for pa, pb in zip(pose[a], pose[b]))
            spheres.append(Sphere(center, ra + (rb - ra) * u, material, side, u, length))  # type: ignore[arg-type]
    return spheres


def _raycast(camera: Camera, placement: Placement, spheres: List[Sphere]) -> Dict[Tuple[int, int], Hit]:
    """Nearest sphere per pixel (orthographic shading per sphere, perspective placement)."""
    hits: Dict[Tuple[int, int], Hit] = {}
    for sphere in spheres:
        cx, cy, cz = world_point(placement, sphere.center)
        depth = cz - camera.z
        if depth < NEAR + sphere.radius:
            continue
        sx, sy = camera.project(cx, cy, cz)
        r_px = camera.focal * sphere.radius / depth
        for py in range(int(sy - r_px), int(sy + r_px) + 1):
            for px in range(int(sx - r_px), int(sx + r_px) + 1):
                dx, dy = (px + 0.5 - sx) / r_px, (py + 0.5 - sy) / r_px
                q = dx * dx + dy * dy
                if q > 1:
                    continue
                nz = math.sqrt(1 - q)
                hit_depth = depth - sphere.radius * nz
                best = hits.get((px, py))
                if best is None or hit_depth < best.depth:
                    normal = _unrotate((dx, -dy, -nz), placement.roll, placement.pitch, placement.yaw)
                    point = tuple(c + sphere.radius * n for c, n in zip(sphere.center, normal))
                    hits[(px, py)] = Hit(hit_depth, sphere, normal, r_px, point)  # type: ignore[arg-type]
    return hits


def _surface(hit: Hit) -> SurfaceHit:
    s = hit.sphere
    return SurfaceHit(s.material, s.side, s.along, s.limb_len, hit.normal, hit.point,
                      s.radius / hit.radius_px, hit.radius_px)


def _shade(hit: Hit, placement: Placement, pose: Skeleton) -> RGB:
    """Three-tone cel shading plus rim light on edges turned towards the city."""
    base = suit_color(_surface(hit), pose)
    if base in UNSHADED:
        return base
    world_n = _rotate(hit.normal, placement.roll, placement.pitch, placement.yaw)
    diffuse = sum(a * b for a, b in zip(world_n, KEY_LIGHT))
    tone = TONES[0] if diffuse < 0.2 else TONES[1] if diffuse < 0.6 else TONES[2]
    color = tuple(round(c * tone) for c in base)
    rim = sum(a * b for a, b in zip(world_n, RIM_LIGHT))
    if rim > 0.0 and world_n[2] > -0.35:
        color = tuple(round(c + (r - c) * 0.45) for c, r in zip(color, RIM))
    return color  # type: ignore[return-value]


def draw_hero3d(canvas: Canvas, camera: Camera, pose: Skeleton, placement: Placement) -> None:
    """Rasterize the posed hero onto the canvas, outline included."""
    hits = _raycast(camera, placement, body_spheres(pose))
    outline = {
        (x + dx, y + dy)
        for (x, y) in hits
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        if (x + dx, y + dy) not in hits
    }
    for x, y in outline:
        canvas.put(x, y, OUTLINE)
    for (x, y), hit in hits.items():
        canvas.put(x, y, _shade(hit, placement, pose))
