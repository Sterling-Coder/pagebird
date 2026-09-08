"""Translation-quality metrics — axis A, model-based.

Reference-free is the realistic default here: the pipeline produces target text
for documents nobody has hand-translated, so there is usually no gold reference
to score against. **COMET-KIWI** needs only (source, target) and is the headline
number for that case.

When references *do* exist they come from the review loop itself — every
human-approved segment is written back to the TM by `review.store.update_segment`,
so `babel_tm.db` accumulates a gold corpus for free. `runner.freeze_gold_from_tm`
snapshots it to JSONL. Two rules for that corpus:

  * freeze it and score against the snapshot, never the live TM, or the numbers
    move under you between runs;
  * a segment that came back as `tm_hit` was *served* from the TM, so scoring it
    against that same TM entry measures the cache, not the engine. `chrf` and
    `comet` exclude `tm_hit` segments for exactly this reason.

BLEU is available but not reported by default: these segments are short (labels,
headings, "Answers"), and sentence-level BLEU on a five-token string is close to
noise. chrF++ handles both short strings and Spanish morphology far better.

All metrics here degrade to `available: false` when their package is missing —
the zero-dependency integrity tier must stay runnable on a bare checkout.
"""

from __future__ import annotations

import json
import os

from babel import languages
from babel.eval.integrity import SHIPPED, restored

# Reference-free QE. Note: the wmt22/23 KIWI checkpoints are gated on Hugging
# Face — `huggingface-cli login` once, or override with BABEL_EVAL_KIWI_MODEL.
KIWI_MODEL = os.environ.get("BABEL_EVAL_KIWI_MODEL", "Unbabel/wmt22-cometkiwi-da")
# Reference-based COMET. Ungated.
COMET_MODEL = os.environ.get("BABEL_EVAL_COMET_MODEL", "Unbabel/wmt22-comet-da")

# sacreBLEU tokenizers that matter for the languages in languages.py. Scoring a
# Japanese or Chinese hypothesis with the default `13a` tokenizer produces a
# meaningless number, so this mapping is not optional cosmetics.
_TOKENIZERS = {"ja": "ja-mecab", "zh": "zh", "ko": "ko-mecab"}


def pairs(segments: list[dict], exclude_tm: bool = False) -> list[dict]:
    """Restored (source, target) pairs ready for a model.

    Restoring placeholders first is essential: a model handed `⟦=3/4⟧` sees a
    corrupt token where the real text has a number, and scores it as such.
    """
    out = []
    for s in segments:
        if s["status"] not in SHIPPED or not (s.get("target") or "").strip():
            continue
        if exclude_tm and s["status"] == "tm_hit":
            continue
        src = restored(s["source"], s["placeholders"]).strip()
        tgt = restored(s["target"], s["placeholders"]).strip()
        if src and tgt:
            out.append({"seg_id": s["seg_id"], "src": src, "mt": tgt})
    return out


def load_gold(path: str) -> dict[str, str]:
    """JSONL of {"source": ..., "target": ...} keyed by restored source text."""
    gold: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            gold[row["source"].strip()] = row["target"]
    return gold


def _with_refs(items: list[dict], gold: dict[str, str]) -> list[dict]:
    return [dict(it, ref=gold[it["src"]]) for it in items if it["src"] in gold]


# --- surface metrics -------------------------------------------------------


def surface(segments: list[dict], gold: dict[str, str], lang: str = "es",
            with_bleu: bool = False) -> dict:
    """chrF++ and TER against gold references (sacreBLEU)."""
    try:
        import sacrebleu
    except ImportError:
        return {"available": False, "reason": "pip install sacrebleu"}

    items = _with_refs(pairs(segments, exclude_tm=True), gold)
    if not items:
        return {"available": True, "matched": 0,
                "reason": "no shipped non-TM segment matched a gold reference"}

    hyps = [it["mt"] for it in items]
    refs = [[it["ref"] for it in items]]
    result = {
        "available": True,
        "matched": len(items),
        # chrF++ (word_order=2) — character n-grams plus word bigrams. Robust on
        # short strings and on the morphology of Romance/Slavic targets.
        "chrf2": round(sacrebleu.CHRF(word_order=2).corpus_score(hyps, refs).score, 2),
        # Translation edit rate — post-editing effort, lower is better.
        "ter": round(sacrebleu.TER().corpus_score(hyps, refs).score, 2),
    }
    if with_bleu:
        tok = _TOKENIZERS.get(languages.get(lang).code, "13a")
        result["bleu"] = round(
            sacrebleu.BLEU(tokenize=tok).corpus_score(hyps, refs).score, 2)
        result["bleu_tokenizer"] = tok
        result["bleu_caveat"] = ("regression tracking only — unreliable as an "
                                 "absolute score on segments this short")
    return result


# --- neural metrics --------------------------------------------------------


def _predict(model_name: str, data: list[dict], batch_size: int, gpus: int):
    from comet import download_model, load_from_checkpoint

    model = load_from_checkpoint(download_model(model_name))
    return model.predict(data, batch_size=batch_size, gpus=gpus, progress_bar=False)


def _distribution(scores: list[float], items: list[dict], threshold: float) -> dict:
    ranked = sorted(zip(scores, items), key=lambda p: p[0])
    return {
        "mean": round(sum(scores) / len(scores), 4),
        "median": round(sorted(scores)[len(scores) // 2], 4),
        "p10": round(sorted(scores)[int(len(scores) * 0.1)], 4),
        "below_threshold": sum(1 for s in scores if s < threshold),
        "threshold": threshold,
        "worst": [{"seg_id": it["seg_id"], "score": round(sc, 4),
                   "src": it["src"][:100], "mt": it["mt"][:100]}
                  for sc, it in ranked[:20]],
    }


def comet_kiwi(segments: list[dict], model: str = KIWI_MODEL, max_segments: int = 2000,
               batch_size: int = 16, gpus: int = 0, threshold: float = 0.75) -> dict:
    """Reference-free quality estimation — the headline axis-A number.

    Per-segment 0–1. `worst` is directly actionable: it is the review queue
    ordered by predicted quality rather than by pipeline status, which is what
    makes this worth running even without any gold data.
    """
    items = pairs(segments)[:max_segments]
    if not items:
        return {"available": True, "scored": 0, "reason": "no shipped segments"}
    try:
        out = _predict(model, [{"src": it["src"], "mt": it["mt"]} for it in items],
                       batch_size, gpus)
    except ImportError:
        return {"available": False, "reason": "pip install unbabel-comet"}
    except Exception as exc:  # gated checkpoint, no HF token, OOM, no disk
        return {"available": False, "model": model, "reason": str(exc)[:300]}

    scores = [float(s) for s in out.scores]
    return {"available": True, "model": model, "scored": len(scores),
            "system_score": round(float(out.system_score), 4),
            **_distribution(scores, items, threshold)}


def comet(segments: list[dict], gold: dict[str, str], model: str = COMET_MODEL,
          max_segments: int = 2000, batch_size: int = 16, gpus: int = 0,
          threshold: float = 0.80) -> dict:
    """Reference-based COMET — best human correlation available, needs gold."""
    items = _with_refs(pairs(segments, exclude_tm=True), gold)[:max_segments]
    if not items:
        return {"available": True, "scored": 0,
                "reason": "no shipped non-TM segment matched a gold reference"}
    try:
        out = _predict(model, [{"src": it["src"], "mt": it["mt"], "ref": it["ref"]}
                               for it in items], batch_size, gpus)
    except ImportError:
        return {"available": False, "reason": "pip install unbabel-comet"}
    except Exception as exc:
        return {"available": False, "model": model, "reason": str(exc)[:300]}

    scores = [float(s) for s in out.scores]
    return {"available": True, "model": model, "scored": len(scores),
            "system_score": round(float(out.system_score), 4),
            **_distribution(scores, items, threshold)}


# --- roll-up ---------------------------------------------------------------


def evaluate(segments: list[dict], lang: str = "es", gold_path: str | None = None,
             neural: bool = True, with_bleu: bool = False, gpus: int = 0,
             max_segments: int = 2000) -> dict:
    """Axis A. `neural=False` keeps this to sacreBLEU (seconds, no model download)."""
    gold = load_gold(gold_path) if gold_path and os.path.exists(gold_path) else {}
    result: dict = {
        "gold_references": len(gold),
        "gold_path": gold_path,
        "surface": surface(segments, gold, lang, with_bleu=with_bleu) if gold else
                   {"available": True, "matched": 0, "reason": "no gold corpus supplied"},
    }
    if neural:
        result["comet_kiwi"] = comet_kiwi(segments, gpus=gpus, max_segments=max_segments)
        result["comet"] = (comet(segments, gold, gpus=gpus, max_segments=max_segments)
                           if gold else
                           {"available": True, "scored": 0,
                            "reason": "no gold corpus supplied"})
    else:
        for key in ("comet_kiwi", "comet"):
            result[key] = {"available": False, "reason": "neural metrics disabled"}
    return result
