"""Summarise the approved Prototype 2 human scores transparently.

Two rules govern every number here:

1. **A blank is NOT SCORED, never a zero.** Blank cells are excluded from every
   mean and the surviving `n` is printed beside it, so a dimension averaged over
   three rows is never mistaken for one averaged over nine.
2. **Objective measurements and human scores are reported separately.** This
   script touches only the human scores. VRAM, latency and the similarity
   indicators live in `docs/evidence/prototype-2/` and are never blended into a
   rubric average.

Writes `docs/evidence/EXP-015-scoring/human-scores.md`.

Run:
    .venv/Scripts/python.exe scripts/summarise_p2_human_scores.py
"""

import csv
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT_DIR = REPO / "docs" / "evidence" / "EXP-015-scoring"
SOURCE = OUT_DIR / "human-scores.csv"

DIMENSIONS = [
    "prompt_adherence", "style_consistency", "reference_influence", "visual_quality",
    "decal_suitability", "composition", "artefacts", "originality",
    "diversity_across_seeds", "copy_or_overfitting_risk",
]

METHOD_ORDER = ["text-only", "img2img", "ip-adapter", "ip-adapter-plus"]


def load() -> list[dict]:
    with open(SOURCE, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def mean_of(rows: list[dict], dimension: str) -> tuple[float | None, int]:
    """Mean over SCORED cells only, with the surviving count."""
    values = [int(r[dimension]) for r in rows if (r.get(dimension) or "").strip()]
    return (statistics.mean(values) if values else None), len(values)


def fmt(value: float | None, count: int) -> str:
    return "not scored" if value is None else f"{value:.2f} (n={count})"


def usable_midrange(rows: list[dict]) -> list[dict]:
    """Controllability condition 4: at least one intermediate level scoring BOTH
    reference_influence >= 3 AND prompt_adherence >= 3. This is the actual product
    requirement - a method that can only choose between ignoring the reference and
    ignoring the prompt is not controllable."""
    out = []
    for r in rows:
        ref, prompt = (r.get("reference_influence") or ""), (r.get("prompt_adherence") or "")
        if ref and prompt and int(ref) >= 3 and int(prompt) >= 3:
            out.append(r)
    return out


def main() -> int:
    rows = load()
    lines = [
        "# Prototype 2 human rubric scores (approved by Kylian, 2026-08-01)",
        "",
        "Authoritative record: [`human-scores.csv`](human-scores.csv). These are **aggregate**",
        "scores at (method x influence level x resolution), which is the granularity the review",
        "was actually performed at. They are **not** per-image scores and must never be presented",
        "as such.",
        "",
        "## How blanks are handled",
        "",
        "**A blank cell means NOT SCORED. It is never a zero and is never back-filled.** Blanks",
        "are excluded from every mean below, and the surviving `n` is printed beside each figure",
        "so a dimension averaged over three rows cannot be mistaken for one averaged over nine.",
        "",
        "Specifically:",
        "",
        "- `reference_influence` and `copy_or_overfitting_risk` are blank for **text-only**, which",
        "  uses no reference image at all.",
        "- `diversity_across_seeds` was scored only where the multi-seed sheet supported it, so it",
        "  carries a much smaller `n` than the other dimensions.",
        "- **text-only at 512x1536 is entirely unscored.** It was not visually rescored from the M4",
        "  contact sheets. **No M3 value has been substituted for it**, and none may be: the M3",
        "  review used different sheets and a different question. It stays not scored.",
        "",
        "## Objective measurements are reported separately",
        "",
        "Nothing on this page is a measurement. VRAM, latency, effective steps, the process-isolation",
        "spot check, the lower-bound diagnostic and the similarity indicators live in",
        "`docs/evidence/prototype-2/` and in `docs/evidence/EXP-014/`. Measured figures and human",
        "judgements are never averaged together or traded off inside a single number.",
        "",
        "## Per-method means at 512x512 (blanks excluded)",
        "",
        "| dimension | " + " | ".join(METHOD_ORDER) + " |",
        "|---|" + "---|" * len(METHOD_ORDER),
    ]

    for dimension in DIMENSIONS:
        cells = []
        for method in METHOD_ORDER:
            subset = [r for r in rows if r["method"] == method and r["resolution"] == "512x512"]
            cells.append(fmt(*mean_of(subset, dimension)))
        lines.append(f"| {dimension} | " + " | ".join(cells) + " |")

    lines += [
        "",
        "Row counts at 512x512: " + ", ".join(
            f"{m} {len([r for r in rows if r['method'] == m and r['resolution'] == '512x512'])}"
            for m in METHOD_ORDER
        ) + ".",
        "",
        "**These means average across influence levels**, including the deliberately weak and",
        "deliberately extreme ones, so they describe a method's behaviour across its whole range",
        "rather than at its best setting. The selected operating point is judged from the rows",
        "themselves, not from these column averages.",
        "",
        "## Scores at the deck format 512x1536",
        "",
        "| method | " + " | ".join(d[:20] for d in DIMENSIONS) + " |",
        "|---|" + "---|" * len(DIMENSIONS),
    ]
    for row in [r for r in rows if r["resolution"] == "512x1536"]:
        cells = [(row.get(d) or "").strip() or "-" for d in DIMENSIONS]
        lines.append(f"| {row['method']} {row['influence_level']} | " + " | ".join(cells) + " |")

    lines += [
        "",
        "`-` means not scored. The text-only row is blank throughout for the reason given above.",
        "",
        "## Controllability condition 4 - a usable mid-range",
        "",
        "The product requirement: at least one intermediate level must score **both**",
        "`reference_influence >= 3` **and** `prompt_adherence >= 3`. A method that can only choose",
        "between ignoring the reference and ignoring the prompt is not controllable.",
        "",
        "| method | level | value | resolution | reference_influence | prompt_adherence |",
        "|---|---|---|---|---|---|",
    ]
    passing = usable_midrange(rows)
    for row in passing:
        lines.append(
            f"| {row['method']} | {row['influence_level']} | {row['strength_value'] or 'n/a'} | "
            f"{row['resolution']} | {row['reference_influence']} | {row['prompt_adherence']} |"
        )

    by_method: dict[str, int] = {}
    for row in passing:
        by_method[row["method"]] = by_method.get(row["method"], 0) + 1
    lines += [
        "",
        "Settings meeting the condition, by method: "
        + ", ".join(f"**{m}** {by_method.get(m, 0)}" for m in METHOD_ORDER if m != "text-only")
        + ".",
        "",
        "## Per-row scores",
        "",
        "| method | level | value | resolution | " + " | ".join(DIMENSIONS) + " |",
        "|---|---|---|---|" + "---|" * len(DIMENSIONS),
    ]
    for row in rows:
        cells = [(row.get(d) or "").strip() for d in DIMENSIONS]
        lines.append(
            f"| {row['method']} | {row['influence_level']} | {row['strength_value'] or '-'} | "
            f"{row['resolution']} | " + " | ".join(cells) + " |"
        )

    lines += ["", "## Reviewer notes, verbatim", ""]
    for row in rows:
        note = (row.get("note") or "").strip()
        if note:
            lines.append(
                f"- **{row['method']} {row['influence_level']} "
                f"{row['strength_value'] or 'n/a'} @ {row['resolution']}** — {note}"
            )
    lines.append("")

    path = OUT_DIR / "human-scores.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"human scores .. {path}")
    print(f"{len(rows)} aggregate rows; {len(passing)} settings meet controllability condition 4")
    blank = sum(1 for r in rows for d in DIMENSIONS if not (r.get(d) or "").strip())
    print(f"{blank} cells recorded as NOT SCORED (excluded from every mean, never zeroed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
