"""Assemble the README animation: every frame rendered once, packed into one PNG
sprite sheet embedded in an SVG, flipped through with a CSS steps() animation.

Why an SVG around a PNG: GitHub strips scripts but keeps CSS animation in SVG
images; `image-rendering: pixelated` keeps the pixel art crisp at any width;
vector rain and a lightning flash ride on top for free. Identical frames (the
idle perch) are stored once. With prefers-reduced-motion the first frame stays.
"""

from __future__ import annotations

import base64
from typing import Dict, List, Tuple

from animation import choreography, weather
from animation.frame import FRAME_HEIGHT, FRAME_WIDTH, render_frame
from animation.png import encode_png
from animation.world import avenue

SCALE = 4
ALT = ("Pixel-art Spider-Man perched on a rooftop leaps into a rainy Times Square-like avenue "
       "and web-swings past billboards of Ruby, Python, JavaScript, C++, Hugging Face and AppSec")


def render_unique_frames() -> Tuple[List[List[bytes]], List[int]]:
    """(distinct frames as RGB rows, frame index shown at each sample time)."""
    times = choreography.sample_times()
    states = [choreography.hero_at(t) for t in times]
    cameras = choreography.camera_track(times, states)
    city = avenue()
    unique: List[List[bytes]] = []
    seen: Dict[Tuple[bytes, ...], int] = {}
    order = []
    for t, state, camera in zip(times, states, cameras):
        rows = render_frame(camera, city, state.view(), choreography.scroll_at(t)).to_rows()
        key = tuple(rows)
        if key not in seen:
            seen[key] = len(unique)
            unique.append(rows)
        order.append(seen[key])
    return unique, order


def flip_keyframes(order: List[int], loop_seconds: float) -> str:
    """Keyframes moving the sheet up one frame height per change, held with steps().

    >>> flip_keyframes([0, 0, 1], 3.0)
    '@keyframes flip{0%{transform:translateY(0px)}66.667%{transform:translateY(-100px)}100%{transform:translateY(-100px)}}'
    """
    count = len(order)
    stops = [(i, frame) for i, frame in enumerate(order) if i == 0 or frame != order[i - 1]]
    body = "".join(
        f"{round(i / count * 100, 3):g}%{{transform:translateY({-frame * FRAME_HEIGHT}px)}}" for i, frame in stops
    )
    body += f"100%{{transform:translateY({-order[-1] * FRAME_HEIGHT}px)}}"
    return f"@keyframes flip{{{body}}}"


def _style(order: List[int]) -> str:
    seconds = f"{choreography.LOOP_SECONDS:.3f}s"
    rules = [
        f".sheet{{animation:flip {seconds} steps(1,end) infinite}}",
        flip_keyframes(order, choreography.LOOP_SECONDS),
        weather.rain_css(weather.BACK_RAIN, FRAME_HEIGHT),
        weather.rain_css(weather.FRONT_RAIN, FRAME_HEIGHT),
        weather.flash_css(choreography.LOOP_SECONDS),
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}",
    ]
    return "<style>" + "".join(rules) + "</style>"


def build_svg() -> str:
    """The complete animated SVG document."""
    frames, order = render_unique_frames()
    sheet_png = encode_png(FRAME_WIDTH, [row for frame in frames for row in frame])
    data = base64.b64encode(sheet_png).decode("ascii")
    image = (
        f'<image width="{FRAME_WIDTH}" height="{FRAME_HEIGHT * len(frames)}" preserveAspectRatio="none" '
        f'style="image-rendering:optimizeSpeed;image-rendering:-moz-crisp-edges;image-rendering:pixelated" '
        f'href="data:image/png;base64,{data}"/>'
    )
    rain = "".join(weather.render_rain(layer, FRAME_WIDTH, FRAME_HEIGHT) for layer in (weather.BACK_RAIN, weather.FRONT_RAIN))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FRAME_WIDTH} {FRAME_HEIGHT}" '
        f'width="{FRAME_WIDTH * SCALE}" height="{FRAME_HEIGHT * SCALE}" role="img" aria-label="{ALT}">'
        f"{_style(order)}"
        f'<defs><clipPath id="frame"><rect width="{FRAME_WIDTH}" height="{FRAME_HEIGHT}" rx="4"/></clipPath></defs>'
        f'<g clip-path="url(#frame)"><g class="sheet">{image}</g>{rain}'
        f"{weather.render_flash(FRAME_WIDTH, FRAME_HEIGHT)}</g></svg>"
    )
