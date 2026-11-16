"""CLI: regenerate the README animation.

Usage: python3 -m animation [output_path]   (default: spiderman.svg)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from animation.sheet import build_svg


def main(argv: List[str]) -> int:
    output = Path(argv[1] if len(argv) > 1 else "spiderman.svg")
    svg = build_svg()
    output.write_text(svg, encoding="utf-8")
    print(f"wrote {output} ({len(svg.encode()) / 1024:.1f} KiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
