"""Checks run on the reconstructed image before it is written.

Each check reports rather than repairs: a failure is a finding in the job
report for a person to look at, and the image is still delivered. The checks
are deliberately plain — pixel arithmetic, not perceptual metrics.
"""

from __future__ import annotations

import logging
import re

import numpy as np

from pagebirdy.image.regions import TextRegion

logger = logging.getLogger("pagebirdy.image.quality")


def _check(name: str, passed: bool, detail: str = "") -> dict:
    return {"name": name, "passed": bool(passed), "detail": detail}


def run_checks(original: np.ndarray, output: np.ndarray, regions: list[TextRegion],
               work_boxes: dict[str, tuple[int, int, int, int]]) -> dict:
    checks = []

    checks.append(_check("dimensions_unchanged", original.shape == output.shape,
                         f"{original.shape[1]}×{original.shape[0]} → {output.shape[1]}×{output.shape[0]}"))

    # Nothing outside a region the pipeline rewrote may differ by a single level.
    outside = np.ones(original.shape[:2], dtype=bool)
    for x0, y0, x1, y1 in work_boxes.values():
        outside[y0:y1, x0:x1] = False
    changed = int(np.count_nonzero(np.any(original[outside] != output[outside], axis=-1))) \
        if original.shape == output.shape else -1
    checks.append(_check("unrelated_pixels_unchanged", changed == 0,
                         f"{changed} pixel(s) changed outside translated regions"))

    intended = [r for r in regions if r.action == "translate" and r.target]
    drawn = [r for r in intended if r.render.get("drawn")]
    checks.append(_check("all_regions_processed", len(drawn) == len(intended),
                         f"{len(drawn)} of {len(intended)} translated region(s) redrawn"))

    outside_box = [r.id for r in drawn if not r.render.get("inside_box")]
    checks.append(_check("text_inside_bounding_boxes", not outside_box,
                         ", ".join(outside_box) or "every redrawn region fits its box"))

    clipped = [r.id for r in drawn if r.render.get("fit", {}).get("forced")]
    checks.append(_check("no_clipped_or_forced_text", not clipped,
                         ", ".join(clipped) or "no region needed forced scaling"))

    blank = [r.id for r in drawn if r.render.get("ink_pixels", 0) == 0]
    checks.append(_check("no_blank_regions", not blank,
                         ", ".join(blank) or "every redrawn region carries ink"))

    low = [r.id for r in regions if r.content_type == "low_confidence"]
    checks.append(_check("ocr_confidence", not low,
                         (f"{len(low)} region(s) below the confidence threshold: " + ", ".join(low))
                         if low else "every region above the threshold"))

    return {"passed": all(c["passed"] for c in checks), "checks": checks}


def _norm(text: str) -> str:
    return re.sub(r"[\W_]+", "", (text or "").lower())


def verify_with_ocr(output_regions: list[TextRegion], regions: list[TextRegion]) -> dict:
    """Read the output back and see whether each redrawn translation is there.

    A region counts as verified when the text OCR reads inside its box shares
    at least half its characters with what was drawn (order-insensitive, so a
    line wrapped differently by the reader still counts). Advisory only — OCR
    reading a fresh render is not ground truth either.
    """
    results = []
    for r in regions:
        if not r.render.get("drawn"):
            continue
        x0, y0, x1, y1 = r.render["box"]
        found = " ".join(o.text for o in output_regions
                         if o.bbox[0] < x1 and o.bbox[2] > x0 and o.bbox[1] < y1 and o.bbox[3] > y0)
        want, got = _norm(r.target), _norm(found)
        common = sum(min(want.count(c), got.count(c)) for c in set(want))
        score = common / len(want) if want else 1.0
        results.append({"id": r.id, "expected": r.target, "read": found,
                        "score": round(score, 2), "verified": score >= 0.5})
    verified = sum(1 for x in results if x["verified"])
    return {"ran": True, "verified": verified, "total": len(results), "regions": results}
