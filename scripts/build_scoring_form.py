"""Build the blank rubric scoring form for the Prototype 1 human-review gate.

Qualitative evaluation is the student's own research judgement (learning
outcomes D1/D4/D6), so this script deliberately produces an EMPTY form. It
never writes, estimates, or suggests a score, and it never names a winner.

Emits, into docs/evidence/EXP-006-scoring/:
  - scoring-form.md   human-friendly tables, one row per (model, track, prompt)
  - scoring-form.csv  same rows, for tallying afterwards
  - rubric.md         the 9 dimensions and their 1-5 anchors, copied from
                      docs/05-experiment-methodology.md so the form is
                      self-contained when reviewing images

Run:
    .venv/Scripts/python.exe scripts/build_scoring_form.py
"""

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.evaluation import prompt_kit  # noqa: E402
from ml.inference.bench_schema import MODELS, STATUS_OK, read_jsonl  # noqa: E402

EVIDENCE = REPO / "docs" / "evidence"
COMBINED = EVIDENCE / "prototype-1"
OUT_DIR = EVIDENCE / "EXP-006-scoring"

# The 9 dimensions defined in docs/05-experiment-methodology.md.
DIMENSIONS: list[tuple[str, str, str]] = [
    ("prompt_adherence", "ignores prompt", "matches all stated elements"),
    ("style_consistency", "style unrecognizable", "unmistakably the target style"),
    ("reference_influence", "no visible relation to reference", "clear, controllable influence"),
    ("visual_quality", "broken/blurry", "clean, coherent"),
    ("decal_suitability", "unusable on a deck", "print-ready composition for a deck"),
    ("composition", "chaotic/cropped badly", "balanced for the deck format"),
    ("artefacts", "dominant artefacts", "none visible"),
    ("originality", "near-copy of a source", "clearly new artwork"),
    ("diversity_across_seeds", "mode-collapsed", "varied yet on-style"),
]

# Not applicable in Prototype 1: there is no reference image until Prototype 2.
NOT_APPLICABLE_IN_P1 = {"reference_influence"}


def load_rows() -> list[dict]:
    combined = COMBINED / "results-all-candidates.csv"
    if combined.exists():
        with open(combined, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    rows: list[dict] = []
    for exp_dir in sorted(EVIDENCE.glob("EXP-00*")):
        for jsonl in sorted(exp_dir.glob("results-*.jsonl")):
            rows += read_jsonl(jsonl)
    return rows


def scoreable_units(rows: list[dict]) -> list[dict]:
    """One scoring unit per (model, track, resolution, prompt): the student scores
    a fixed-seed group of images together, as the methodology prescribes."""
    seen: dict[tuple, dict] = {}
    for row in rows:
        if row["status"] != STATUS_OK:
            continue
        key = (row["model_repo_id"], row["track"], row["width"], row["height"], row["prompt_id"])
        entry = seen.setdefault(
            key,
            {
                "model_repo_id": row["model_repo_id"],
                "track": row["track"],
                "resolution": f"{row['width']}x{row['height']}",
                "prompt_id": row["prompt_id"],
                "memory_tier": row["memory_tier"],
                "seeds": [],
                "images": [],
            },
        )
        entry["seeds"].append(str(row["seed"]))
        if row.get("output_path"):
            entry["images"].append(row["output_path"])
    for entry in seen.values():
        entry["seeds"] = ",".join(sorted(set(entry["seeds"]), key=int))
        entry["images"] = "; ".join(sorted(entry["images"]))
    return [seen[k] for k in sorted(seen)]


def slug_for(repo_id: str) -> str:
    for spec in MODELS.values():
        if spec.repo_id == repo_id:
            return spec.slug
    return repo_id.replace("/", "-")


def write_rubric() -> Path:
    lines = [
        "# Prototype 1 evaluation rubric (1-5 per dimension)",
        "",
        "Copied from `docs/05-experiment-methodology.md` so this form is self-contained.",
        "Score each dimension 1-5 using the anchors below. Scores are the student's;",
        "they are never estimated or filled in by the assistant.",
        "",
        "| dimension | 1 | 5 | applies in Prototype 1? |",
        "|---|---|---|---|",
    ]
    for name, low, high in DIMENSIONS:
        applies = "no - no reference image until Prototype 2" if name in NOT_APPLICABLE_IN_P1 else "yes"
        lines.append(f"| {name} | {low} | {high} | {applies} |")
    lines += [
        "",
        "## How to score",
        "",
        "1. Open the Track A cross-model sheet: all candidates at 512x512, same prompts, same seed.",
        "   This is the controlled comparison - use it for like-for-like judgement.",
        "2. Open the Track B cross-model sheet: each candidate at the resolution it was",
        "   designed for. Use this for quality judgement, so SDXL is not penalised for a",
        "   size it was never built for.",
        "3. For each row in `scoring-form.md`, view the fixed-seed group listed in `images`",
        "   and enter one score per dimension.",
        "4. `diversity_across_seeds` is judged across the seed group as a whole, not per image.",
        "",
        "Track A and Track B scores are reported separately in DR-007 and must not be averaged",
        "together - the trade-off between them is the actual finding.",
        "",
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "rubric.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_forms(units: list[dict]) -> tuple[Path, Path]:
    active = [name for name, _, _ in DIMENSIONS if name not in NOT_APPLICABLE_IN_P1]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = OUT_DIR / "scoring-form.csv"
    fieldnames = ["model", "track", "resolution", "prompt_id", "memory_tier", "seeds", *active, "notes"]
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for unit in units:
            writer.writerow(
                {
                    "model": slug_for(unit["model_repo_id"]),
                    "track": unit["track"],
                    "resolution": unit["resolution"],
                    "prompt_id": unit["prompt_id"],
                    "memory_tier": unit["memory_tier"],
                    "seeds": unit["seeds"],
                    **{name: "" for name in active},
                    "notes": "",
                }
            )

    lines = [
        "# Prototype 1 scoring form (BLANK - to be filled in by Kylian)",
        "",
        f"Frozen kit fingerprint: `{prompt_kit.kit_fingerprint()}`",
        "",
        "Every score cell is intentionally empty. See `rubric.md` for the 1-5 anchors and",
        "the recommended order of review. `reference_influence` is omitted: there is no",
        "reference image until Prototype 2.",
        "",
        "Scale: 1 = worst, 5 = best. Leave a cell blank if you cannot judge it.",
        "",
    ]
    for track in sorted({unit["track"] for unit in units}):
        lines += [f"## Track {track}", ""]
        header = "| model | resolution | prompt | tier | seeds | " + " | ".join(active) + " | notes |"
        lines.append(header)
        lines.append("|" + "---|" * (len(active) + 6))
        for unit in [u for u in units if u["track"] == track]:
            lines.append(
                f"| {slug_for(unit['model_repo_id'])} | {unit['resolution']} | {unit['prompt_id']} | "
                f"{unit['memory_tier']} | {unit['seeds']} | " + " | " * 0
                + " | ".join("" for _ in active)
                + " |  |"
            )
        lines.append("")

    lines += [
        "## Image locations",
        "",
        "Full-resolution PNGs are git-ignored under `outputs/EXP-###/`. The committed",
        "cross-model contact sheets are in `docs/evidence/prototype-1/`.",
        "",
        "| model | track | prompt | images |",
        "|---|---|---|---|",
    ]
    for unit in units:
        lines.append(
            f"| {slug_for(unit['model_repo_id'])} | {unit['track']} | {unit['prompt_id']} | {unit['images']} |"
        )
    lines.append("")

    md_path = OUT_DIR / "scoring-form.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path, csv_path


def main() -> int:
    rows = load_rows()
    if not rows:
        print("no benchmark results found - run scripts/run_benchmarks.py first", file=sys.stderr)
        return 1
    units = scoreable_units(rows)
    if not units:
        print("no successful runs to score", file=sys.stderr)
        return 1

    rubric = write_rubric()
    md_path, csv_path = write_forms(units)
    print(f"rubric ........ {rubric}")
    print(f"scoring form .. {md_path}")
    print(f"scoring csv ... {csv_path}")
    print(f"{len(units)} scoring units across {len({u['model_repo_id'] for u in units})} candidates")
    print("\nAll score cells are blank by design. Scores are the student's judgement.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
