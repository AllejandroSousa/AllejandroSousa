"""Minimal indexed-colour PNG encoder (stdlib only: zlib + struct).

Pixel art uses few colours, so an 8-bit palette (1 byte per pixel, filter
"None") compresses about 2.5x better than RGB here. If the image has more than
256 colours, the rarest ones are mapped to their nearest kept colour (for the
README animation that touches ~100 of 2.6M pixels).
"""

from __future__ import annotations

import struct
import zlib
from collections import Counter
from typing import Dict, List, Tuple

RGB = Tuple[int, int, int]
MAX_COLORS = 256


def _chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def _pixels(row: bytes) -> List[bytes]:
    return [row[i : i + 3] for i in range(0, len(row), 3)]


def build_palette(rows: List[bytes]) -> Tuple[List[bytes], Dict[bytes, int]]:
    """Most common colours (max 256) and a map from every colour to its index.

    >>> palette, index = build_palette([b"\\x00\\x00\\x00\\xff\\xff\\xff"])
    >>> len(palette), index[b"\\xff\\xff\\xff"]
    (2, 1)
    """
    counts = Counter(pixel for row in rows for pixel in _pixels(row))
    palette = [color for color, _ in counts.most_common(MAX_COLORS)]
    index = {color: i for i, color in enumerate(palette)}
    for color in counts:
        if color not in index:
            nearest = min(palette, key=lambda kept: sum((a - b) ** 2 for a, b in zip(kept, color)))
            index[color] = index[nearest]
    return palette, index


def encode_png(width: int, rows: List[bytes]) -> bytes:
    """Encode RGB rows (3 bytes per pixel) as an 8-bit palette PNG.

    >>> encode_png(1, [b"\\x00\\x00\\x00"])[:8] == b"\\x89PNG\\r\\n\\x1a\\n"
    True
    """
    for number, row in enumerate(rows):
        if len(row) != width * 3:
            raise ValueError(f"row {number} has {len(row)} bytes; expected {width * 3} (RGB x {width})")
    palette, index = build_palette(rows)
    header = struct.pack(">IIBBBBB", width, len(rows), 8, 3, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(index[p] for p in _pixels(row)) for row in rows)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"PLTE", b"".join(palette))
        + _chunk(b"IDAT", zlib.compress(raw, 9))
        + _chunk(b"IEND", b"")
    )
