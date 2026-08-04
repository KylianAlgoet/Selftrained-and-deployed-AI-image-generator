"""Build the BLINDED Prototype 4 gate-1 review package.

Produces, in one pass (the plan listed a sheets script and a form script; they are
combined because the blinding map must be generated exactly once and shared):

  * one contact sheet per blinded arm/checkpoint,
  * a blank scoring form referring ONLY to blind labels,
  * a mapping file, written to a SEPARATE path, that Kylian opens after scoring.

**What is blinded and what is not.** Style cannot be hidden - a ukiyo-e sheet
looks like ukiyo-e. What must be hidden is everything the review is actually
comparing: which minimal-geometric sheet is style-only and which is dataset-v1
verbatim (EXP-023), which is the 12-, 24- or 44-image arm (EXP-024), and whether a
sheet is the 150- or 300-step checkpoint. All of those are masked behind labels
like `GEO-3`, assigned by a seeded shuffle within each style.

The base SD 1.5 reference sheets are NOT blinded and are labelled as such: they
are the control, and knowing which one is the untrained model is the point.

**The form ships blank.** No score is pre-filled, no arm is marked as preferred,
and no visual-quality claim appears anywhere in this package.

Run:
    .venv/Scripts/python.exe scripts/build_p4_review_package.py
"""

import csv
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.dataset.contact_sheet import make_contact_sheet  # noqa: E402
from ml.training import style_kit  # noqa: E402

GENERATIONS = REPO / "docs" / "evidence" / "EXP-025" / "pilot-matrix.jsonl"
SHEETS = REPO / "docs" / "evidence" / "prototype-4" / "pilot-sheets"
FORM = REPO / "docs" / "evidence" / "prototype-4" / "pilot-scoring-form.md"
# Deliberately NOT inside the sheets folder Kylian browses while scoring.
MAPPING = REPO / "docs" / "evidence" / "EXP-025" / "BLINDING-MAP-do-not-open-before-scoring.csv"

# Fixed so the blinding is reproducible from the repository alone.
BLINDING_SEED = 20260804

STYLE_TAG = {"minimal-geometric": "GEO", "ukiyo-e": "UKY", "retro-poster": "PST"}

RUBRIC = [
    ("prompt_adherence", "ignores prompt", "matches all stated elements"),
    ("style_consistency", "style unrecognizable", "unmistakably the target style"),
    ("visual_quality", "broken/blurry", "clean, coherent"),
    ("decal_suitability", "unusable on a deck", "print-ready for a deck"),
    ("composition", "chaotic/cropped badly", "balanced for the deck format"),
    ("artefacts", "dominant artefacts", "none visible"),
    ("originality", "near-copy of a source", "clearly new artwork"),
    ("diversity_across_seeds", "mode-collapsed", "varied yet on-style"),
    ("copy_or_overfitting_risk", "reproduces training data", "clearly independent"),
]

FAILURE_MODES = [
    "pseudo_text",
    "unwanted_frame",
    "background_transfer",
    "repeated_motifs",
    "vertical_stretching",
]


def main() -> int:
    if not GENERATIONS.is_file():
        print(f"missing {GENERATIONS}")
        return 1
    rows = [json.loads(line) for line in GENERATIONS.open(encoding="utf-8") if line.strip()]

    # Group by (arm, checkpoint) - one sheet per group.
    groups: dict[tuple[str, int], list[dict]] = {}
    for row in rows:
        groups.setdefault((row["arm"], row["checkpoint_step"]), []).append(row)

    trained = {k: v for k, v in groups.items() if not k[0].startswith("BASE-")}
    base = {k: v for k, v in groups.items() if k[0].startswith("BASE-")}

    # Blind within style: shuffle the (arm, checkpoint) pairs of each style.
    by_style: dict[str, list[tuple[str, int]]] = {}
    for key, recs in trained.items():
        by_style.setdefault(recs[0]["style"], []).append(key)

    rng = random.Random(BLINDING_SEED)
    labels: dict[tuple[str, int], str] = {}
    for style in style_kit.STYLE_ORDER:
        keys = sorted(by_style.get(style, []))
        rng.shuffle(keys)
        for n, key in enumerate(keys, start=1):
            labels[key] = f"{STYLE_TAG[style]}-{n}"

    SHEETS.mkdir(parents=True, exist_ok=True)
    MAPPING.parent.mkdir(parents=True, exist_ok=True)

    # Deterministic cell order, documented in the form so a reviewer knows what
    # each tile is without the filename telling them which arm it came from.
    def cell_sort(record: dict):
        return (record["prompt_id"], record["seed"], record["lora_weight"] or 0.0)

    sheet_index = []
    for key, recs in sorted(trained.items()):
        label = labels[key]
        ordered = sorted(recs, key=cell_sort)
        paths = [REPO / r["output_path"] for r in ordered]
        out = SHEETS / f"{label}.jpg"
        make_contact_sheet(paths, out, columns=4)
        sheet_index.append((label, recs[0]["style"], len(ordered), out))
        print(f"  {label:8s} {recs[0]['style']:18s} {len(ordered):2d} images -> {out.name}")

    for key, recs in sorted(base.items()):
        style = recs[0]["style"]
        label = f"BASE-{STYLE_TAG[style]}"
        ordered = sorted(recs, key=cell_sort)
        out = SHEETS / f"{label}.jpg"
        make_contact_sheet([REPO / r["output_path"] for r in ordered], out, columns=4)
        sheet_index.append((label, style, len(ordered), out))
        print(f"  {label:8s} {style:18s} {len(ordered):2d} images -> {out.name} (control, not blinded)")

    # --- the mapping, kept away from the scoring sheet -----------------------
    with MAPPING.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["blind_label", "arm", "checkpoint_step", "style", "note"])
        for key, label in sorted(labels.items(), key=lambda kv: kv[1]):
            arm, step = key
            note = {
                "EXP-020": "style-only captions, 44 images",
                "EXP-023": "dataset-v1 verbatim captions, 44 images (caption A/B counterpart)",
                "EXP-024n12": "style-only captions, 12 images (RQ4 size arm)",
                "EXP-024n24": "style-only captions, 24 images (RQ4 size arm)",
                "EXP-021": "style-only captions, 44 images",
                "EXP-022": "style-only captions, 36 images",
            }.get(arm, "")
            writer.writerow([label, arm, step, trained[key][0]["style"], note])
    print(f"\nmapping -> {MAPPING.relative_to(REPO)}")

    # --- the blank form ------------------------------------------------------
    lines = [
        "# Prototype 4 — pilot scoring form (BLANK, BLINDED)",
        "",
        "**Gate 1.** Score the sheets in `pilot-sheets/`, then open the mapping at",
        f"`{MAPPING.relative_to(REPO).as_posix()}`. **Not before** — the mapping is what the",
        "blinding protects.",
        "",
        "## What is blinded",
        "",
        "Style is visible and cannot be hidden. Everything the comparison is actually about is",
        "hidden: which `GEO-*` sheet uses style-only versus dataset-v1 verbatim captions, which is",
        "the 12-, 24- or 44-image arm, and whether a sheet is the 150- or 300-step checkpoint.",
        f"Labels were assigned by a seeded shuffle within each style (seed {BLINDING_SEED}), so the",
        "blinding is reproducible from the repository alone.",
        "",
        "**One disclosed weakness.** The shuffle happened to place a few same-arm pairs at adjacent",
        "labels, so adjacent numbers *may* be one arm at its two checkpoints. **The seed was fixed",
        "before the draw and has not been re-rolled** — re-drawing until the arrangement looked",
        "better would be exactly the kind of tampering the blinding exists to prevent. This does not",
        "weaken what matters: adjacency reveals nothing about *which* arm a sheet is, so style-only",
        "versus verbatim and 12 versus 24 versus 44 remain fully masked. Treat adjacent labels as",
        "unrelated.",
        "",
        "`BASE-*` sheets are the untrained SD 1.5 control on the identical prompt text, and are",
        "deliberately **not** blinded.",
        "",
        "## Sheet layout",
        "",
        "Every trained sheet holds 8 images in 4 columns, ordered deterministically by",
        "**(prompt, seed, LoRA weight)**:",
        "",
        "| cell | prompt | seed | weight |",
        "|---|---|---|---|",
    ]
    cell = 1
    for prompt in style_kit.PILOT_PROMPTS:
        for seed in style_kit.PILOT_SEEDS:
            for weight in style_kit.PILOT_LORA_WEIGHTS:
                lines.append(f"| {cell} | {prompt.id} | {seed} | {weight} |")
                cell += 1
    lines += [
        "",
        "Prompt roles — `VP1-style` is style-matching; `VP2-shared` is the identical subject across",
        "all three styles, so style differences are attributable to the LoRA rather than the prompt.",
        "",
        "## Sheets to score",
        "",
        "| sheet | style | images |",
        "|---|---|---|",
    ]
    for label, style, n, _ in sorted(sheet_index):
        lines.append(f"| `{label}` | {style} | {n} |")

    lines += [
        "",
        "## Rubric (1–5, per `docs/05-experiment-methodology.md`)",
        "",
        "| dimension | 1 | 5 |",
        "|---|---|---|",
    ]
    lines += [f"| `{name}` | {low} | {high} |" for name, low, high in RUBRIC]
    lines += [
        "",
        "**Leave a cell blank if you did not judge it.** A blank is never a zero and will never be",
        "back-filled — the M3/M4 rule. `reference_influence` is deliberately absent: no reference",
        "image is used anywhere in the pilot matrix.",
        "",
        "## Scores",
        "",
        "| sheet | " + " | ".join(f"`{n}`" for n, _, _ in RUBRIC) + " |",
        "|---" * (len(RUBRIC) + 1) + "|",
    ]
    for label, _, _, _ in sorted(sheet_index):
        lines.append(f"| `{label}` | " + " | ".join("" for _ in RUBRIC) + " |")

    lines += [
        "",
        "## Failure-mode probe",
        "",
        "Mark `worse`, `same`, `better` or leave blank, against the `BASE-*` control for that style.",
        "",
        "| sheet | " + " | ".join(f"`{m}`" for m in FAILURE_MODES) + " |",
        "|---" * (len(FAILURE_MODES) + 1) + "|",
    ]
    for label, _, _, _ in sorted(sheet_index):
        if not label.startswith("BASE-"):
            lines.append(f"| `{label}` | " + " | ".join("" for _ in FAILURE_MODES) + " |")

    lines += [
        "",
        "## Decisions this gate needs from you",
        "",
        "These are the decisions Phase B cannot start without. None of them has been made for you.",
        "",
        "1. **Checkpoint per style** — 150 or 300 steps, for each of the three styles.",
        "2. **Full-run step count per style** — within the pre-declared band 600–1500.",
        "3. **Caption strategy verdict** — style-only preferred / verbatim preferred / trade-off /",
        "   tie-inconclusive, per the rules in the approved plan.",
        "4. **Dataset-size verdict** — which of O1 monotone, O2 plateau, O3 no effect,",
        "   O4 trade-off, O5 inconclusive the 12/24/44 arms support.",
        "5. **Contingency** — whether any contingency run is authorised, and if so which SINGLE",
        "   variable it may change (LR, rank/alpha, steps, or caption dropout).",
        "6. **Multi-style** — whether the balanced multi-style run proceeds.",
        "",
        "## Not decided, and not decidable from this package",
        "",
        "- No style has been selected, and no arm is described as better than another.",
        "- No visual-quality claim is made anywhere in Phase A.",
        "- The automated indicators in `docs/evidence/EXP-026/` are descriptive only. They populate",
        "  no cell above, and they may not select a checkpoint or a hyperparameter.",
        "",
    ]
    FORM.write_text("\n".join(lines), encoding="utf-8")
    print(f"form    -> {FORM.relative_to(REPO)}")
    total_kb = sum(p.stat().st_size for _, _, _, p in sheet_index) / 1024
    print(f"{len(sheet_index)} sheets, {total_kb:.0f} KB total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
