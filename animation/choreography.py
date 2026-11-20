"""Timeline of the loop: close-up perch, leap, five swings, rise and land, close-up again.

The hero lands on the same rooftop one city PERIOD further along the avenue,
and the camera returns to the same close-up offset, so the last frame equals
the first and the loop has no cut.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from animation import hero_poses as poses
from animation.camera import Camera
from animation.frame import HeroView
from animation.hero3d import Placement
from animation.world import PERIOD

Vec3 = Tuple[float, float, float]

FPS = 12
IDLE_START = 2.2
LEAP_SECONDS = 0.8
SWING_SECONDS = 1.1
GAP_SECONDS = 0.25
LAND_SECONDS = 1.2
IDLE_END = 0.9

HOME: Vec3 = (17.2, 58.0, 31.2)
PERCH_YAW = -20.0
CLOSE_OFFSET: Vec3 = (-0.85, 1.05, -2.05)
FOLLOW_OFFSET: Vec3 = (0.0, 1.7, -5.0)
CAMERA_SMOOTH_SECONDS = 0.17
FOLLOW_X = 0.55  # in flight the camera drifts only partly with the hero, staying near mid-street
SCROLL_PER_LOOP = 120.0  # code screens scroll this many rows per loop (multiple of 24)

# Where each swing starts/ends, and which side its web anchors to.
SWING_POINTS: Tuple[Vec3, ...] = (
    (-2.0, 36.0, 54.0), (3.0, 35.0, 102.0), (-3.0, 36.0, 150.0),
    (3.0, 35.0, 198.0), (-2.0, 36.0, 246.0), (1.5, 41.0, 292.0),
)  # fmt: skip
SWING_SIDES = (-1, 1, -1, 1, -1)
SWING_DIP = 10.0
SWING_SWAY = 3.0
ANCHOR_HEIGHT = 92.0
ANCHOR_AHEAD = 22.0
LAND_START_SLOPE = 0.7  # matches the speed the old landing curve left the last swing with


@dataclass(frozen=True)
class HeroState:
    """Pose and placement of the hero, plus the web anchor while swinging."""

    pose: poses.Skeleton
    placement: Placement
    web_anchor: Optional[Vec3] = None
    web_hand: str = "r_hand"

    def view(self) -> HeroView:
        return HeroView(self.pose, self.placement, self.web_anchor, self.web_hand)


def smoothstep(u: float) -> float:
    """Ease in-out, clamped to [0, 1]."""
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def lerp3(a: Vec3, b: Vec3, u: float) -> Vec3:
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u))


def bezier3(p0: Vec3, control: Vec3, p1: Vec3, u: float) -> Vec3:
    """Quadratic Bezier in 3D."""
    return lerp3(lerp3(p0, control, u), lerp3(control, p1, u), u)


def landing_home() -> Vec3:
    return (HOME[0], HOME[1], HOME[2] + PERIOD)


def perched(at: Vec3) -> HeroState:
    return HeroState(poses.CROUCH, Placement(at, yaw=PERCH_YAW))


def leap(u: float) -> HeroState:
    """Off the ledge into the avenue: crouch opens into the spread pose."""
    start, end = HOME, SWING_POINTS[0]
    control = ((start[0] + end[0]) / 2, start[1] + 3, (start[2] + end[2]) / 2)
    pose = poses.blend(poses.CROUCH, poses.SPREAD, smoothstep(u / 0.45))
    placement = Placement(bezier3(start, control, end, u), yaw=lerp(PERCH_YAW, 0, smoothstep(u)),
                          pitch=lerp(0, 14, smoothstep(u)))
    return HeroState(pose, placement)


def _swing_pose(side: int, u: float) -> poses.Skeleton:
    """Spread at catch and release, hanging in between."""
    hang = poses.SWING_RIGHT if side > 0 else poses.SWING_LEFT
    weight = smoothstep(u / 0.18) * smoothstep((1 - u) / 0.18)
    return poses.blend(poses.SPREAD, hang, weight)


def swing(index: int, u: float) -> HeroState:
    """Pendulum-like swing: slow at catch/release, fastest and lowest in the middle."""
    start, end = SWING_POINTS[index], SWING_POINTS[index + 1]
    side = SWING_SIDES[index]
    eased = u - 0.6 * math.sin(2 * math.pi * u) / (2 * math.pi)
    arc = math.sin(math.pi * u)
    position = (
        lerp(start[0], end[0], eased) + side * SWING_SWAY * arc,
        lerp(start[1], end[1], eased) - SWING_DIP * arc,
        lerp(start[2], end[2], eased),
    )
    anchor = (side * 14.0, ANCHOR_HEIGHT, (start[2] + end[2]) / 2 + ANCHOR_AHEAD)
    placement = Placement(position, roll=-side * 16 * arc, pitch=10)
    hand = "r_hand" if side > 0 else "l_hand"
    return HeroState(_swing_pose(side, u), placement, anchor, hand)


def gap(index: int, u: float) -> HeroState:
    """Brief free flight between releasing one web and catching the next."""
    position = SWING_POINTS[index + 1]
    lifted = (position[0], position[1] + 1.5 * math.sin(math.pi * u), position[2])
    return HeroState(poses.SPREAD, Placement(lifted, pitch=10))


def arrive(u: float, start_slope: float = LAND_START_SLOPE) -> float:
    """Cubic Hermite from 0 to 1 leaving at `start_slope` and arriving at rest.

    >>> arrive(0.0), arrive(1.0)
    (0.0, 1.0)
    """
    return start_slope * (u ** 3 - 2 * u ** 2 + u) + 3 * u ** 2 - 2 * u ** 3


def land(u: float) -> HeroState:
    """Last release flings the hero up onto the rooftop, back into the perch.

    The path eases out to zero speed: arriving at full speed and freezing on the
    next frame read as a hard cut right before the loop restarts.
    """
    start, end = SWING_POINTS[-1], landing_home()
    control = ((start[0] + end[0]) / 2, end[1] + 6, (start[2] + end[2]) / 2)
    pose = poses.blend(poses.SPREAD, poses.CROUCH, smoothstep((u - 0.55) / 0.4))
    placement = Placement(bezier3(start, control, end, arrive(u)),
                          yaw=lerp(0, PERCH_YAW, smoothstep((u - 0.4) / 0.6)),
                          pitch=lerp(10, 0, smoothstep(u)))
    return HeroState(pose, placement)


def _schedule() -> List[Tuple[float, float, object]]:
    """(start, end, state function of u) for every segment, in order."""
    segments: List[Tuple[float, float, object]] = [(0.0, IDLE_START, lambda u: perched(HOME))]
    t = IDLE_START
    segments.append((t, t + LEAP_SECONDS, leap))
    t += LEAP_SECONDS
    for i in range(len(SWING_SIDES)):
        segments.append((t, t + SWING_SECONDS, lambda u, i=i: swing(i, u)))
        t += SWING_SECONDS
        if i < len(SWING_SIDES) - 1:
            segments.append((t, t + GAP_SECONDS, lambda u, i=i: gap(i, u)))
            t += GAP_SECONDS
    segments.append((t, t + LAND_SECONDS, land))
    t += LAND_SECONDS
    # Back at HOME, not HOME + PERIOD: the city is identical there, and using the
    # very same coordinates makes the last frame match the first pixel for pixel
    # (shifting by PERIOD left float round-off flipping a few pixels at the seam).
    segments.append((t, t + IDLE_END, lambda u: perched(HOME)))
    return segments


SCHEDULE = _schedule()
LOOP_SECONDS = SCHEDULE[-1][1]
TRAVEL = (IDLE_START, SCHEDULE[-1][0])


def hero_at(t: float) -> HeroState:
    """Hero state at time t in [0, LOOP_SECONDS]."""
    for start, end, state_at in SCHEDULE:
        if start <= t <= end:
            return state_at((t - start) / (end - start))  # type: ignore[operator]
    raise ValueError(f"time {t} is outside the loop [0, {LOOP_SECONDS}]")


def sample_times() -> List[float]:
    """One instant per frame; the last frame is the one before the loop restarts."""
    count = int(round(LOOP_SECONDS * FPS))
    return [i / FPS for i in range(count)]


def _unwrapped(t: float, state: HeroState) -> Vec3:
    """Hero position continuous along z (the final idle is stored one PERIOD back)."""
    x, y, z = state.placement.position
    return (x, y, z + PERIOD) if t >= TRAVEL[1] else (x, y, z)


def _smoothed(points: List[Vec3]) -> List[Vec3]:
    """Short centred moving average (removes jitter from the follow camera)."""
    radius = max(1, int(CAMERA_SMOOTH_SECONDS * FPS))
    smoothed = []
    for i in range(len(points)):
        window = points[max(0, i - radius): i + radius + 1]
        smoothed.append(tuple(sum(p[k] for p in window) / len(window) for k in range(3)))
    return smoothed  # type: ignore[return-value]


def _flight_weight(t: float) -> float:
    """0 on the perch (close-up), 1 in flight (follow cam), eased in between."""
    land_start = TRAVEL[1] - LAND_SECONDS * 0.6
    leaving = smoothstep((t - IDLE_START) / LEAP_SECONDS)
    arriving = smoothstep((t - land_start) / (TRAVEL[1] - land_start))
    return leaving * (1 - arriving)


def camera_track(times: List[float], states: List[HeroState]) -> List[Camera]:
    """Close-up offset from the hero on the perch, smoothed follow cam in flight.

    Anchoring every frame to the hero keeps him in shot during the leap and the
    landing, where a camera easing between fixed points would lag behind.
    """
    unwrapped = [_unwrapped(t, s) for t, s in zip(times, states)]
    follow = _smoothed(unwrapped)
    cameras = []
    for t, state, raw, (fx, fy, fz) in zip(times, states, unwrapped, follow):
        weight = _flight_weight(t)
        if weight == 0:
            raw = state.placement.position  # exact perch coordinates (seamless loop)
        close = (raw[0] + CLOSE_OFFSET[0], raw[1] + CLOSE_OFFSET[1], raw[2] + CLOSE_OFFSET[2])
        chase = (FOLLOW_X * fx + FOLLOW_OFFSET[0], fy + FOLLOW_OFFSET[1], fz + FOLLOW_OFFSET[2])
        cameras.append(Camera(*lerp3(close, chase, weight)))
    return cameras


def scroll_at(t: float) -> float:
    """Code-screen scroll: advances only while travelling, a whole pattern per loop."""
    progress = (t - TRAVEL[0]) / (TRAVEL[1] - TRAVEL[0])
    return SCROLL_PER_LOOP * min(1.0, max(0.0, progress))

