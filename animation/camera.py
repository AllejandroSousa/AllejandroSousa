"""Pinhole camera looking down +z (the avenue), with no roll or pitch.

World units: x to the right, y up, z forward along the avenue. Screen y grows
downward; the horizon sits at `horizon` pixels from the top.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

NEAR = 1.0


@dataclass(frozen=True)
class Camera:
    """Camera position plus the screen it projects onto."""

    x: float
    y: float
    z: float
    focal: float = 110.0
    screen_width: int = 240
    horizon: float = 34.0

    def depth(self, z: float) -> float:
        """Distance along the view axis."""
        return z - self.z

    def project(self, x: float, y: float, z: float) -> Optional[Tuple[float, float]]:
        """Screen (x, y) of a world point, or None if it is behind the near plane.

        >>> Camera(0, 10, 0).project(0, 10, 50)
        (120.0, 34.0)
        """
        d = self.depth(z)
        if d < NEAR:
            return None
        scale = self.focal / d
        return (self.screen_width / 2 + (x - self.x) * scale, self.horizon - (y - self.y) * scale)

    def screen_x(self, x: float, z: float) -> float:
        """Screen x only (z must be in front of the near plane)."""
        return self.screen_width / 2 + (x - self.x) * self.focal / self.depth(z)

    def screen_y(self, y: float, z: float) -> float:
        """Screen y only (z must be in front of the near plane)."""
        return self.horizon - (y - self.y) * self.focal / self.depth(z)
