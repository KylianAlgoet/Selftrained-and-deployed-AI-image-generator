"""Audit the Prototype 4 training captions and source images, before any training.

This is the recorded justification for the style-only caption strategy and the
baseline for hypothesis H4 (does `retro-poster` carry frames and pseudo-text into
a trained LoRA?). It is evidence gathered BEFORE the runs, not a rationalisation
written afterwards.

Three passes, each labelled honestly:

1. **Caption classification** - deterministic rules over the dataset-v1 content
   phrase. Rule-based, so it is reproducible and auditable, and its limits are
   stated: it detects the SHAPE of a caption, not whether the words are true of
   the image.

2. **Border-darkness INDICATOR** - an objective measurement, not a verdict. Mean
   luminance of the outer border ring versus the interior. A framed or matted
   scan photographed against a dark surround shows a large negative delta. It
   flags candidates for inspection; it does not prove an image is framed, and it
   never decides anything.

3. **Geometry** - orientation and aspect distribution per style, which is what
   made 512x512 training the selected condition.

Run:
    .venv/Scripts/python.exe scripts/build_caption_audit.py
"""

import csv
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.dataset.captions import STYLE_PHRASES  # noqa: E402
from ml.training import style_kit  # noqa: E402

MANIFEST_DIR = REPO / "data" / "manifests"
EVIDENCE = REPO / "docs" / "evidence" / "prototype-4"

SUFFIX = "skateboard decal artwork, "

# A caption ending on a dangling function word was cut off mid-phrase.
DANGLING = re.compile(r"\b(of|and|the|from|in|at|with|a|to|by|for|on|its)$", re.IGNORECASE)
ATTRIBUTION = re.compile(r"\bby\s+[a-z]", re.IGNORECASE)
VENUE = re.compile(
    r"\b(auditorium|theatre|theater|municipal|hall|opera|playhouse|federal|project|wpa|"
    r"long beach|new york|chicago|boston)\b",
    re.IGNORECASE,
)

# Border ring width as a fraction of the shorter side.
BORDER_FRACTION = 0.06
# Pre-declared: a border this much darker than the interior is FLAGGED for
# inspection. Chosen before any image was measured.
DARK_BORDER_DELTA = 25.0


def classify(content: str) -> str:
    text = content.strip()
    if not text:
        return "empty"
    if DANGLING.search(text):
        return "truncated"
    if ATTRIBUTION.search(text):
        return "attribution"
    if VENUE.search(text):
        return "venue-or-archive"
    return "visual"


def border_stats(path: Path) -> tuple[float, float, float] | None:
    """(border mean luminance, interior mean luminance, delta). Indicator only."""
    try:
        import numpy as np
        from PIL import Image

        with Image.open(path) as image:
            grey = image.convert("L")
            grey.thumbnail((512, 512), Image.LANCZOS)
            a = np.asarray(grey, dtype=np.float64)
    except Exception:  # noqa: BLE001 - a measurement failure must not stop the audit
        return None

    h, w = a.shape
    b = max(2, int(round(min(h, w) * BORDER_FRACTION)))
    if h <= 2 * b or w <= 2 * b:
        return None
    interior = a[b:-b, b:-b]
    total = float(a.sum())
    inner = float(interior.sum())
    n_total = a.size
    n_inner = interior.size
    border_mean = (total - inner) / (n_total - n_inner)
    interior_mean = inner / n_inner
    return border_mean, interior_mean, border_mean - interior_mean


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Prototype 4 — caption and source-image audit",
        "",
        "**Date:** 2026-08-04 · **Milestone:** M6 · Gathered **before** any training run.",
        "",
        "This audit is the recorded justification for the style-only caption strategy and the",
        "baseline for **H4** (does `retro-poster` carry frames and pseudo-text into a trained",
        "LoRA?). `dataset-v1.csv` was opened read-only; nothing here modifies it.",
        "",
        "## 1. Caption classification (rule-based)",
        "",
        "Deterministic rules over the dataset-v1 **content phrase** — the part after",
        f"`{SUFFIX.strip()}`. **Stated limit: these rules detect the SHAPE of a caption, not",
        "whether its words are true of the image.** A phrase classified `visual` is not thereby",
        "verified as accurate.",
        "",
        "| class | rule |",
        "|---|---|",
        "| `truncated` | ends on a dangling function word (`…of`, `…and`, `…from`) |",
        "| `attribution` | contains `by <name>` — an authorship credit, not a description |",
        "| `venue-or-archive` | names a venue, city, or archive programme |",
        "| `visual` | none of the above |",
        "",
    ]

    detail_rows: list[dict] = []
    summary: list[dict] = []

    for spec in sorted(style_kit.STYLES, key=lambda s: s.order):
        style = spec.key
        path = MANIFEST_DIR / f"style-{style}-p4.csv"
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        counts = {"visual": 0, "attribution": 0, "truncated": 0, "venue-or-archive": 0, "empty": 0}
        contents = []
        for row in rows:
            content = row["dataset_v1_caption"].split(SUFFIX, 1)[-1]
            cls = classify(content)
            counts[cls] += 1
            contents.append(content)
            detail_rows.append(
                {
                    "id": row["id"],
                    "style": style,
                    "classification": cls,
                    "content_phrase": content,
                    "training_caption": row["training_caption"],
                }
            )
        distinct = len(set(contents))
        summary.append({"style": style, "n": len(rows), "distinct": distinct, **counts})

    lines += ["| style | items | distinct phrases | visual | attribution | truncated | venue/archive |", "|---|---|---|---|---|---|---|"]
    for s in summary:
        lines.append(
            f"| `{s['style']}` | {s['n']} | **{s['distinct']}** | {s['visual']} | "
            f"**{s['attribution']}** | **{s['truncated']}** | {s['venue-or-archive']} |"
        )

    lines += [
        "",
        "**What this shows.** `retro-poster` carries the most authorship credits — play titles and",
        "writers rather than anything visible in the image. `ukiyo-e` carries truncated phrases cut",
        "off mid-sentence. `minimal-geometric` captions are accurate and visual but nearly",
        "duplicated: only a handful of distinct phrases across the whole set, because the generator",
        "varies little but the shape count.",
        "",
        "**Consequence.** Training a *style* LoRA on these teaches the trigger proper nouns and",
        "sentence fragments. The frozen strategy is therefore **style-only** captions",
        f"(`{style_kit.build_training_caption(style_kit.LEAD_STYLE, STYLE_PHRASES[style_kit.LEAD_STYLE])}`).",
        "**This remains a hypothesis under test, not a settled fact:** EXP-023 retrains the lead",
        "style on the dataset-v1 captions verbatim, changing nothing else, and both arms are scored",
        "blind against the rules in the plan.",
        "",
        "## 2. Border-darkness indicator (objective measurement, NOT a verdict)",
        "",
        f"Mean luminance of the outer {BORDER_FRACTION:.0%} ring versus the interior, on a 0–255",
        f"scale. **A delta at or below −{DARK_BORDER_DELTA:.0f} is FLAGGED for inspection.** The",
        "threshold was fixed before any image was measured.",
        "",
        "**This is an indicator, not proof.** A dark border can mean a framed or matted scan, or",
        "simply dark artwork at the edges. It flags candidates; it decides nothing, and it never",
        "excludes an image.",
        "",
        "| style | items measured | median delta | flagged (≤ −%.0f) | flagged %% |" % DARK_BORDER_DELTA,
        "|---|---|---|---|---|",
    ]

    border_detail: list[dict] = []
    for spec in sorted(style_kit.STYLES, key=lambda s: s.order):
        style = spec.key
        rows = list(csv.DictReader((MANIFEST_DIR / f"style-{style}-p4.csv").open(encoding="utf-8")))
        deltas = []
        for row in rows:
            stats = border_stats(REPO / row["source_path"])
            if stats is None:
                continue
            border, interior, delta = stats
            deltas.append(delta)
            border_detail.append(
                {
                    "id": row["id"],
                    "style": style,
                    "border_mean_luminance": round(border, 2),
                    "interior_mean_luminance": round(interior, 2),
                    "delta": round(delta, 2),
                    "flagged_dark_border": delta <= -DARK_BORDER_DELTA,
                }
            )
        flagged = sum(1 for d in deltas if d <= -DARK_BORDER_DELTA)
        med = statistics.median(deltas) if deltas else float("nan")
        pct = (100.0 * flagged / len(deltas)) if deltas else 0.0
        lines.append(f"| `{style}` | {len(deltas)} | {med:+.1f} | **{flagged}** | {pct:.0f}% |")

    lines += [
        "",
        "## 3. Source geometry",
        "",
        "| style | items | landscape | portrait | median h/w | items ≥ 2.5:1 tall |",
        "|---|---|---|---|---|---|",
    ]
    for spec in sorted(style_kit.STYLES, key=lambda s: s.order):
        style = spec.key
        rows = list(csv.DictReader((MANIFEST_DIR / f"style-{style}-p4.csv").open(encoding="utf-8")))
        ars = [int(r["height"]) / int(r["width"]) for r in rows]
        land = sum(1 for a in ars if a < 1)
        port = sum(1 for a in ars if a > 1)
        tall = sum(1 for a in ars if a >= 2.5)
        lines.append(
            f"| `{style}` | {len(rows)} | {land} | {port} | {statistics.median(ars):.2f} | {tall} |"
        )

    lines += [
        "",
        "The deck target is **3.00**. Only `minimal-geometric` is already there. This is why",
        "training runs at **512×512 for all three styles**: cropping a 1.33:1 ukiyo-e print to 1:3",
        "would teach a crop artefact rather than a style. Deck geometry comes from generation",
        "(DR-007), which EXP-019 already proved works with a 512×512-trained LoRA.",
        "",
        "## Files",
        "",
        "- `caption-classification.csv` — every training item, its classification and both captions",
        "- `border-darkness-indicator.csv` — per-image border/interior luminance and the flag",
        "- `style-manifest-exclusions.csv` — every dataset-v1 item no training manifest uses",
        "",
    ]

    (EVIDENCE / "caption-audit.md").write_text("\n".join(lines), encoding="utf-8")

    with (EVIDENCE / "caption-classification.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "style", "classification", "content_phrase", "training_caption"])
        w.writeheader()
        w.writerows(detail_rows)

    with (EVIDENCE / "border-darkness-indicator.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["id", "style", "border_mean_luminance", "interior_mean_luminance", "delta", "flagged_dark_border"],
        )
        w.writeheader()
        w.writerows(border_detail)

    for s in summary:
        print(
            f"{s['style']:20s} n={s['n']:3d} distinct={s['distinct']:3d} "
            f"visual={s['visual']:3d} attribution={s['attribution']:3d} truncated={s['truncated']:3d} "
            f"venue={s['venue-or-archive']:3d}"
        )
    flagged_total = sum(1 for r in border_detail if r["flagged_dark_border"])
    print(f"\nborder-darkness flagged: {flagged_total}/{len(border_detail)}")
    print(f"wrote {(EVIDENCE / 'caption-audit.md').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
