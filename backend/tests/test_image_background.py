"""Removing the original text by rebuilding the background behind it."""

import numpy as np

from pagebirdy.image import background


def _canvas(kind):
    h, w = 80, 200
    if kind == "solid":
        arr = np.empty((h, w, 3), np.float32)
        arr[:] = (240, 200, 60)
    elif kind == "gradient":
        ramp = np.linspace(0, 255, w, dtype=np.float32)
        arr = np.stack([np.broadcast_to(ramp, (h, w))] * 3, axis=-1).copy()
    else:
        arr = np.random.default_rng(1).uniform(0, 255, (h, w, 3)).astype(np.float32)
    clean = arr.copy()
    arr[30:50, 50:150] = (10, 10, 10)  # the "text"
    return arr, clean


def test_flat_background_is_filled_with_its_own_colour():
    arr, clean = _canvas("solid")
    rec = background.reconstruct(arr, (50, 30, 150, 50), 20)
    assert rec.strategy == "solid" and not rec.textured
    assert np.abs(rec.patch - clean[30:50, 50:150]).max() < 1


def test_gradient_runs_straight_through_the_removed_text():
    arr, clean = _canvas("gradient")
    rec = background.reconstruct(arr, (50, 30, 150, 50), 20)
    assert rec.strategy == "interpolate" and not rec.textured
    assert np.abs(rec.patch - clean[30:50, 50:150]).mean() < 3


def test_texture_is_flagged_rather_than_hidden():
    arr, _ = _canvas("noise")
    assert background.reconstruct(arr, (50, 30, 150, 50), 20).textured


def test_region_at_the_image_edge_still_reconstructs():
    arr, clean = _canvas("solid")
    rec = background.reconstruct(arr, (0, 0, 60, 20), 20)
    assert rec.patch.shape == (20, 60, 3)
    assert np.abs(rec.patch - clean[0:20, 0:60]).max() < 1


def test_text_colour_is_read_from_the_ink():
    arr, _ = _canvas("solid")
    box = (40, 25, 160, 55)
    rec = background.reconstruct(arr, box, 20)
    style = background.text_style(arr[25:55, 40:160], rec.patch)
    assert style["color"] == (10, 10, 10)
    assert style["ink"] == 20 * 100
    # a 20px-tall bar: stroke = 2·area/perimeter = 2·2000/(2·100 + 2·18) ≈ 17
    assert 15 < style["stroke"] < 20
