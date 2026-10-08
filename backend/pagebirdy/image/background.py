"""Remove the original text from a region by rebuilding what was behind it.

Never a white box: the background is estimated from a ring of pixels just
outside the region, which the text never touched.

* **solid** — the ring is one flat colour (a banner, a label plate): fill with
  its median, which ignores any stray glyph edge that leaked into the ring.
* **interpolate** — the ring varies smoothly (a gradient, vignetting): a Coons
  patch — each interior pixel blended from the four edges around it, so the
  gradient runs straight through where the text was.

A ring with real texture (a photo, a pattern) gets the interpolated patch too,
and the region is flagged: a smooth patch over texture is visible, and that is
for a person to judge. `STRATEGIES` is the extension point; a learned inpainter
is one more entry and one more branch in `choose`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Luminance spread (std, 0-255) of the ring below which it is one flat colour.
_FLAT_STD = 6.0
# Mean step between neighbouring ring pixels above which the ring is texture
# rather than a gradient. A gradient changes slowly however far it travels —
# a full-width 200-level ramp steps under one level per pixel — while texture
# changes from one pixel to the next.
_TEXTURE_STEP = 5.0
# How far the background is allowed to differ from a pixel before that pixel
# counts as ink (RGB Euclidean distance, 0-441). Matches the threshold
# ingest/ocr.py uses to find a glyph's colour against its fill.
_INK_DISTANCE = 60.0


@dataclass
class Reconstruction:
    patch: np.ndarray  # HxWxC float32, the background with the text removed
    strategy: str
    background: tuple[int, ...]  # median ring colour
    ring_std: float
    roughness: float
    textured: bool


def ring_width(line_px: float) -> int:
    return int(max(2, min(12, round(line_px * 0.2))))


def _ring(arr: np.ndarray, box: tuple[int, int, int, int], r: int):
    """The four edge strips around `box` (each may be empty at an image edge)."""
    x0, y0, x1, y1 = box
    h, w = arr.shape[:2]
    top = arr[max(0, y0 - r):y0, x0:x1]
    bottom = arr[y1:min(h, y1 + r), x0:x1]
    left = arr[y0:y1, max(0, x0 - r):x0]
    right = arr[y0:y1, x1:min(w, x1 + r)]
    return top, bottom, left, right


def _luma(px: np.ndarray) -> np.ndarray:
    if px.shape[-1] >= 3:
        return px[..., 0] * 0.299 + px[..., 1] * 0.587 + px[..., 2] * 0.114
    return px[..., 0]


def roughness(strips) -> float:
    """Mean luminance step between neighbouring pixels along each ring strip."""
    top, bottom, left, right = strips
    steps = []
    for strip, axis in ((top, 1), (bottom, 1), (left, 0), (right, 0)):
        if strip.size and strip.shape[axis] > 1:
            steps.append(float(np.mean(np.abs(np.diff(_luma(strip), axis=axis)))))
    return float(np.median(steps)) if steps else 0.0


def choose(ring_std: float) -> str:
    return "solid" if ring_std < _FLAT_STD else "interpolate"


def reconstruct(arr: np.ndarray, box: tuple[int, int, int, int], line_px: float) -> Reconstruction:
    """The region `box` (x0, y0, x1, y1, ints, in bounds) with its text removed."""
    x0, y0, x1, y1 = box
    c = arr.shape[2]
    strips = _ring(arr, box, ring_width(line_px))
    ring_px = np.concatenate([s.reshape(-1, c) for s in strips if s.size], axis=0) \
        if any(s.size for s in strips) else arr[y0:y1, x0:x1].reshape(-1, c)
    background = np.median(ring_px, axis=0)
    ring_std = float(np.std(_luma(ring_px)))
    strategy = choose(ring_std)
    hh, ww = y1 - y0, x1 - x0

    if strategy == "solid":
        patch = np.broadcast_to(background, (hh, ww, c)).astype(np.float32).copy()
    else:
        patch = _coons(strips, background, hh, ww, c)

    rough = roughness(strips)
    return Reconstruction(patch=patch, strategy=strategy,
                          background=tuple(int(round(v)) for v in background),
                          ring_std=ring_std, roughness=rough, textured=rough > _TEXTURE_STEP)


def _coons(strips, background, hh: int, ww: int, c: int) -> np.ndarray:
    """Bilinearly blended Coons patch from the four edge strips.

    Each edge is the median across its strip's thickness, so a glyph's
    anti-aliased fringe that crept past the OCR box does not streak through the
    fill. A missing edge (the region touches the image border) takes the
    opposite edge, or the ring median when both are gone.
    """
    top, bottom, left, right = strips
    fallback_row = np.broadcast_to(background, (ww, c)).astype(np.float32)
    fallback_col = np.broadcast_to(background, (hh, c)).astype(np.float32)
    t = np.median(top, axis=0).astype(np.float32) if top.size else None
    b = np.median(bottom, axis=0).astype(np.float32) if bottom.size else None
    l = np.median(left, axis=1).astype(np.float32) if left.size else None
    r = np.median(right, axis=1).astype(np.float32) if right.size else None
    t = t if t is not None else (b if b is not None else fallback_row)
    b = b if b is not None else t
    l = l if l is not None else (r if r is not None else fallback_col)
    r = r if r is not None else l

    u = (np.arange(ww, dtype=np.float32) + 0.5) / ww  # 0..1 across
    v = (np.arange(hh, dtype=np.float32) + 0.5) / hh  # 0..1 down
    U = u[None, :, None]
    V = v[:, None, None]
    T, B = t[None, :, :], b[None, :, :]
    L, R = l[:, None, :], r[:, None, :]
    tl, tr = (t[0] + l[0]) / 2, (t[-1] + r[0]) / 2
    bl, br = (b[0] + l[-1]) / 2, (b[-1] + r[-1]) / 2
    corners = ((1 - U) * (1 - V) * tl + U * (1 - V) * tr
               + (1 - U) * V * bl + U * V * br)
    patch = (1 - V) * T + V * B + (1 - U) * L + U * R - corners
    return np.clip(patch, 0, 255).astype(np.float32)


def ink_mask(original: np.ndarray, background: np.ndarray) -> np.ndarray:
    """Pixels of `original` that differ from the rebuilt background: the text."""
    diff = original[..., :3].astype(np.float32) - background[..., :3].astype(np.float32)
    return np.sqrt((diff ** 2).sum(axis=-1)) > _INK_DISTANCE


def stroke_width(mask: np.ndarray) -> float:
    """Mean stroke thickness of the ink in `mask`, in pixels: twice its area
    over its perimeter (a stroke of width w and length L has area wL and a
    perimeter of about 2L). Scales with the type size only linearly, where
    ink area scales with its square, so a size estimate a few percent off
    barely moves it."""
    mask = mask.astype(bool)
    area = int(mask.sum())
    if not area:
        return 0.0
    padded = np.pad(mask, 1)
    inner = (padded[1:-1, 1:-1] & padded[:-2, 1:-1] & padded[2:, 1:-1]
             & padded[1:-1, :-2] & padded[1:-1, 2:])
    perimeter = area - int(inner.sum())
    return 2.0 * area / max(1, perimeter)


def text_style(original: np.ndarray, background: np.ndarray) -> dict:
    """The original text's colour and how many pixels its ink covers.

    Colour: the median of the most strongly inked pixels, skipping the
    anti-aliased fringe that is half background. The stroke width feeds
    `render.looks_bold`, which decides the weight against a reference.
    """
    mask = ink_mask(original, background)
    if not mask.any():
        bg = np.median(background.reshape(-1, background.shape[-1])[:, :3], axis=0)
        dark = float(_luma(bg[None, :])[0]) > 128
        return {"color": (0, 0, 0) if dark else (255, 255, 255), "ink": 0, "stroke": 0.0}
    diff = np.sqrt(((original[..., :3].astype(np.float32)
                     - background[..., :3].astype(np.float32)) ** 2).sum(axis=-1))
    strong = diff >= np.percentile(diff[mask], 50)
    pick = mask & strong
    color = tuple(int(round(v)) for v in np.median(original[..., :3][pick], axis=0))
    # Each pixel's coverage, as the share of the full text-to-background
    # contrast it reaches. Stroke width is measured at half coverage — the
    # same cut the rendered references are measured at — so an anti-aliased
    # fringe counts the same on both sides of the comparison.
    contrast = np.sqrt(((np.array(color, dtype=np.float32)
                         - background[..., :3].astype(np.float32)) ** 2).sum(axis=-1))
    coverage = diff / np.maximum(contrast, 1.0)
    return {"color": color, "ink": int(np.count_nonzero(mask)),
            "stroke": stroke_width(coverage > 0.5)}
