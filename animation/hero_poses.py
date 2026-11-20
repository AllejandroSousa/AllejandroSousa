"""Skeleton poses for the 3D hero, in metres, hero-local frame.

Local frame: x to the hero's right, y up, z forward (the hero faces +z, away
from the camera). The origin is the point the motion timeline moves: the feet
contact point for the crouch, the pelvis area for airborne poses.
"""

from __future__ import annotations

from typing import Dict, Tuple

Vec3 = Tuple[float, float, float]
Skeleton = Dict[str, Vec3]

JOINTS = (
    "head", "neck", "chest", "pelvis",
    "l_sho", "l_elb", "l_hand", "r_sho", "r_elb", "r_hand",
    "l_hip", "l_knee", "l_foot", "r_hip", "r_knee", "r_foot", "gaze",
)  # fmt: skip
# "gaze" is not a body part: the mask's eyes face from "head" towards it.

# Deep squat, both hands planted on the ledge (the left one just inside the
# left knee), right knee wide, left knee low and forward, head turned left.
CROUCH: Skeleton = {
    "head": (-0.03, 0.97, 0.30), "neck": (0.0, 0.85, 0.22), "chest": (0.03, 0.63, 0.12),
    "pelvis": (0.03, 0.34, -0.04),
    "l_sho": (-0.18, 0.79, 0.14), "l_elb": (-0.22, 0.46, 0.34), "l_hand": (-0.10, 0.06, 0.42),
    "r_sho": (0.22, 0.76, 0.14), "r_elb": (0.34, 0.46, 0.26), "r_hand": (0.30, 0.06, 0.32),
    "l_hip": (-0.09, 0.32, -0.04), "l_knee": (-0.24, 0.22, 0.34), "l_foot": (-0.32, 0.05, -0.04),
    "r_hip": (0.15, 0.32, -0.04), "r_knee": (0.50, 0.38, 0.12), "r_foot": (0.40, 0.05, 0.02),
    "gaze": (-0.85, 1.05, 0.95),
}  # fmt: skip

# Hanging from the web with the right hand; legs tucked, one knee forward.
SWING_RIGHT: Skeleton = {
    "head": (-0.03, 1.67, 0.05), "neck": (0.0, 1.53, 0.02), "chest": (0.0, 1.33, 0.0),
    "pelvis": (0.0, 1.00, 0.0),
    "l_sho": (-0.20, 1.45, 0.0), "l_elb": (-0.42, 1.24, 0.06), "l_hand": (-0.56, 1.04, 0.16),
    "r_sho": (0.18, 1.50, 0.0), "r_elb": (0.20, 1.80, 0.02), "r_hand": (0.16, 2.06, 0.04),
    "l_hip": (-0.11, 0.97, 0.0), "l_knee": (-0.16, 0.68, 0.30), "l_foot": (-0.16, 0.38, 0.04),
    "r_hip": (0.11, 0.97, 0.0), "r_knee": (0.14, 0.62, 0.14), "r_foot": (0.12, 0.30, -0.16),
    "gaze": (0.0, 1.62, 1.6),
}  # fmt: skip

# Arms flung forward and out, legs trailing: the leap and the dive.
SPREAD: Skeleton = {
    "head": (0.0, 1.66, 0.12), "neck": (0.0, 1.52, 0.08), "chest": (0.0, 1.33, 0.05),
    "pelvis": (0.0, 1.00, 0.0),
    "l_sho": (-0.20, 1.45, 0.05), "l_elb": (-0.48, 1.60, 0.16), "l_hand": (-0.74, 1.74, 0.26),
    "r_sho": (0.20, 1.45, 0.05), "r_elb": (0.48, 1.60, 0.16), "r_hand": (0.74, 1.74, 0.26),
    "l_hip": (-0.11, 0.97, 0.0), "l_knee": (-0.30, 0.64, -0.10), "l_foot": (-0.44, 0.32, -0.30),
    "r_hip": (0.11, 0.97, 0.0), "r_knee": (0.30, 0.64, -0.10), "r_foot": (0.44, 0.32, -0.30),
    "gaze": (0.0, 1.7, 1.6),
}  # fmt: skip


def mirror(pose: Skeleton) -> Skeleton:
    """Left/right mirror image (used for swings anchored on the left side).

    >>> mirror({"l_hand": (1.0, 2.0, 3.0), "r_hand": (0.0, 0.0, 0.0)})["r_hand"]
    (-1.0, 2.0, 3.0)
    """
    swapped = {}
    for joint, (x, y, z) in pose.items():
        other = "r" + joint[1:] if joint.startswith("l_") else "l" + joint[1:] if joint.startswith("r_") else joint
        swapped[other] = (-x, y, z)
    return swapped


def blend(a: Skeleton, b: Skeleton, u: float) -> Skeleton:
    """Linear blend between two poses (u=0 -> a, u=1 -> b)."""
    return {j: tuple(pa + (pb - pa) * u for pa, pb in zip(a[j], b[j])) for j in a}  # type: ignore[misc]


SWING_LEFT: Skeleton = mirror(SWING_RIGHT)
