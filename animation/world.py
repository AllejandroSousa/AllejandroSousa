"""The avenue: two rows of tall boxes along z, repeating every PERIOD units.

Times Square style: facades are covered in flush screens, and six of them are
big logo billboards, in the order the hero passes them. The hero
ends the loop on the same rooftop one PERIOD further, so the city tiles along z.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Tuple

from animation.logos import all_logos
from animation.screens import WallScreen, logo_billboard, wall_screens_for

PERIOD = 300.0
HALF_STREET = 14.0
SIDEWALK = 3.0
BUILDING_DEPTH = 30.0
BACK_ROW_X = 48.0
BACK_ROW_HEIGHT = 160.0

HOME = (2.0, 32.0, 58.0)  # z0, z1, height of the right-side rooftop the hero starts on
OPEN_VIEW_Z = 30.0  # right-side buildings this close after HOME stay low (clear opening shot)
LOGO_SLOTS = (("L", 52.0), ("R", 92.0), ("L", 132.0), ("R", 172.0), ("L", 212.0), ("R", 252.0))


@dataclass(frozen=True)
class Box:
    """A building: `side` is 'L' or 'R' of the avenue; x0 < x1, z0 < z1."""

    side: str
    x0: float
    x1: float
    z0: float
    z1: float
    height: float
    seed: int
    screens: Tuple[WallScreen, ...] = field(default=())

    @property
    def street_x(self) -> float:
        """x of the wall that faces the avenue."""
        return self.x1 if self.side == "L" else self.x0

    def shifted(self, dz: float) -> "Box":
        """Same building `dz` further along the avenue (screens included)."""
        screens = tuple(screen.shifted(dz) for screen in self.screens)
        return Box(self.side, self.x0, self.x1, self.z0 + dz, self.z1 + dz, self.height, self.seed, screens)

    def with_screens(self, screens: Tuple[WallScreen, ...]) -> "Box":
        return Box(self.side, self.x0, self.x1, self.z0, self.z1, self.height, self.seed, screens)


def _box(side: str, z0: float, z1: float, height: float, rng: random.Random, screens: bool = True) -> Box:
    x0, x1 = (-HALF_STREET - BUILDING_DEPTH, -HALF_STREET) if side == "L" else (HALF_STREET, HALF_STREET + BUILDING_DEPTH)
    walls = tuple(wall_screens_for(z0, z1, height, side == "R", rng)) if screens else ()
    return Box(side, x0, x1, z0, z1, height, rng.randint(0, 10**6), walls)


def _side(side: str, rng: random.Random) -> List[Box]:
    """Buildings of one side for one period, separated by narrow alleys."""
    boxes = []
    z = HOME[1] + 3 if side == "R" else 0.0
    end = PERIOD + (HOME[0] - 2 if side == "R" else 0.0)
    while end - z > 10:
        length = min(rng.uniform(18, 34), end - z - 2)
        height = rng.uniform(70, 150)
        if side == "R" and z < HOME[1] + OPEN_VIEW_Z:
            height = rng.uniform(34, 46)
        boxes.append(_box(side, z, z + length, height, rng))
        z += length + rng.uniform(2.5, 5)
    return boxes


def _attach_logos(boxes: List[Box]) -> List[Box]:
    """Put each logo billboard on the building of its side nearest to the slot's z.

    The billboard replaces the facade's lower screens; screens above it stay.
    """
    result = list(boxes)
    for (side, z), logo in zip(LOGO_SLOTS, all_logos()):
        candidates = [i for i, b in enumerate(result) if b.side == side and b.z1 - b.z0 > 14]
        if not candidates:
            raise ValueError(f"no building on side {side!r} wide enough for the {logo.name} billboard")
        best = min(candidates, key=lambda i: abs((result[i].z0 + result[i].z1) / 2 - z))
        box = result[best]
        billboard = logo_billboard(box.z0, box.z1, logo, side == "R")
        upper = tuple(s for s in box.screens if s.y0 > billboard.y1 + 2)
        result[best] = box.with_screens((billboard,) + upper)
    return result


def avenue() -> List[Box]:
    """All buildings of one period: home rooftop plus both rows with screens and logo billboards."""
    rng = random.Random(9)
    home = _box("R", *HOME, rng=rng, screens=False)
    return _attach_logos([home] + _side("L", rng) + _side("R", rng))


def visible_boxes(boxes: List[Box], camera_z: float, far: float) -> List[Box]:
    """Copies of the periodic city that fall in [camera_z, camera_z + far], far first."""
    first = int((camera_z - PERIOD) // PERIOD)
    last = int((camera_z + far) // PERIOD) + 1
    copies = [b.shifted(k * PERIOD) for k in range(first, last + 1) for b in boxes]
    in_view = [b for b in copies if b.z1 > camera_z and b.z0 < camera_z + far]
    return sorted(in_view, key=lambda b: -b.z0)
