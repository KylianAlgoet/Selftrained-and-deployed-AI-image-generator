"""Build the Prototype 2 contact sheets delivered at the human-review gate.

These sheets are the evidence Kylian actually scores against, so every one of
them ships with an exact grid legend in `contact-sheets.md`: which row is which
condition, which column is which influence level, and in what order. A grid whose
cells cannot be identified is not evidence.

Two reading traps are stated on every relevant sheet rather than left implicit:

  * img2img `strength` is INVERTED - the columns run left to right from weak to
    strong reference influence, which means the strength NUMBER decreases.
  * the level mapping between methods is an assumption under test, not a
    calibrated equivalence. img2img `strength=0.65` and IP-Adapter `scale=0.55`
    are both labelled "medium"; nothing establishes they exert equal influence.

Built with the existing `ml/dataset/contact_sheet.py`. Missing cells are reported
rather than silently skipped, because a sheet with a hole in it would otherwise
misalign every cell after it.

Run:
    .venv/Scripts/python.exe scripts/build_p2_contact_sheets.py
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.dataset.contact_sheet import make_contact_sheet  # noqa: E402
from ml.inference.reference_schema import (  # noqa: E402
    CONDITIONS,
    LEVEL_VALUES,
    REFERENCES,
    STATUS_OK,
    SWEEP_VALUES,
    read_jsonl,
)

EVIDENCE = REPO / "docs" / "evidence"
OUT_DIR = EVIDENCE / "prototype-2"
SEEDS = (42, 1337, 2026)
PRIMARY_SEED = 42

SOURCE_EXPERIMENTS = ("EXP-008", "EXP-008b", "EXP-009", "EXP-009b", "EXP-010",
                      "EXP-011", "EXP-012", "EXP-013")

SWEEP_CONDITIONS = ("C1", "C2", "C3", "C4")
DECK_CONDITIONS = ("C1", "C2", "C4")
COMPARISON_METHODS = ("text-only", "img2img", "ip-adapter", "ip-adapter-plus")


def load_rows() -> list[dict]:
    rows: list[dict] = []
    for exp_id in SOURCE_EXPERIMENTS:
        directory = EVIDENCE / exp_id
        if not directory.exists():
            continue
        for path in sorted(directory.glob("results-*.jsonl")):
            rows.extend(read_jsonl(path))
    return [r for r in rows if r.get("status") == STATUS_OK and r.get("output_path")]


def _matches(row: dict, method: str, condition: str, seed: int, width: int, height: int) -> bool:
    return (
        row["method"] == method
        and row["condition_id"] == condition
        and int(row["seed"]) == seed
        and int(row["width"]) == width
        and int(row["height"]) == height
    )


def find(
    rows: list[dict], method: str, condition: str, seed: int,
    strength: float | None = None, width: int = 512, height: int = 512,
) -> Path | None:
    """The one output for an exact experimental cell.

    Returns None rather than a near miss: a sheet built from approximate matches
    would look complete and mean nothing.
    """
    for row in rows:
        if not _matches(row, method, condition, seed, width, height):
            continue
        if strength is None:
            if row.get("strength_value") in ("", None):
                return REPO / row["output_path"]
            continue
        try:
            if abs(float(row["strength_value"]) - strength) < 1e-9:
                return REPO / row["output_path"]
        except (TypeError, ValueError):
            continue
    return None


class SheetBuilder:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.reports: list[dict] = []

    def build(self, name: str, cells: list[tuple[str, Path | None]], columns: int,
              thumb: int, title: str, row_legend: list[str], column_legend: list[str],
              note: str) -> None:
        missing = [label for label, path in cells if path is None or not path.exists()]
        present = [path for _, path in cells if path is not None and path.exists()]
        if not present:
            print(f"  {name}: SKIPPED - no cells available")
            self.reports.append({"name": name, "title": title, "built": False,
                                 "missing": missing, "cells": len(cells), "note": note,
                                 "row_legend": row_legend, "column_legend": column_legend})
            return
        if missing:
            print(f"  {name}: WARNING - {len(missing)} missing cell(s): {missing[:6]}")

        out = OUT_DIR / name
        make_contact_sheet(present, out, thumb_size=thumb, columns=columns)
        size_kb = out.stat().st_size // 1024
        print(f"  {name}: {len(present)}/{len(cells)} cells, {size_kb} KB")
        self.reports.append({
            "name": name, "title": title, "built": True, "missing": missing,
            "cells": len(cells), "size_kb": size_kb, "columns": columns,
            "row_legend": row_legend, "column_legend": column_legend, "note": note,
        })


def build_all(rows: list[dict]) -> SheetBuilder:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    builder = SheetBuilder(rows)

    # 1. method comparison at medium, one seed -------------------------------
    cells = []
    for condition in SWEEP_CONDITIONS:
        for method in COMPARISON_METHODS:
            strength = None if method == "text-only" else LEVEL_VALUES[method]["medium"]
            cells.append((f"{condition}/{method}",
                          find(rows, method, condition, PRIMARY_SEED, strength)))
    builder.build(
        "method-comparison-medium-seed42.jpg", cells, columns=len(COMPARISON_METHODS), thumb=256,
        title="Method comparison at the medium influence level, seed 42, 512x512",
        row_legend=[f"row {i + 1} = {c} ({CONDITIONS[c].purpose})" for i, c in enumerate(SWEEP_CONDITIONS)],
        column_legend=[
            "column 1 = text-only baseline (no reference)",
            "column 2 = img2img, strength 0.65",
            "column 3 = IP-Adapter, scale 0.55",
            "column 4 = IP-Adapter-Plus, scale 0.55",
        ],
        note="The 'medium' label is an assumption under test: nothing establishes that "
             "img2img 0.65 and IP-Adapter 0.55 exert comparable influence.",
    )

    # 2 & 3. the two strength sweeps -----------------------------------------
    for method, name in (("img2img", "sweep-img2img-seed42.jpg"),
                         ("ip-adapter", "sweep-ipadapter-seed42.jpg")):
        values = SWEEP_VALUES[method]
        # Ascending reference influence left to right. For img2img that means the
        # strength NUMBER descends, which is exactly the trap being guarded.
        ordered = sorted(values, reverse=method == "img2img")
        cells = [
            (f"{condition}/{value}", find(rows, method, condition, PRIMARY_SEED, value))
            for condition in SWEEP_CONDITIONS
            for value in ordered
        ]
        param = "strength" if method == "img2img" else "scale"
        builder.build(
            name, cells, columns=len(ordered), thumb=224,
            title=f"{method} reference-strength sweep, seed 42, 512x512",
            row_legend=[f"row {i + 1} = {c}" for i, c in enumerate(SWEEP_CONDITIONS)],
            column_legend=[f"column {i + 1} = {param} {v}" for i, v in enumerate(ordered)],
            note=("Columns run left to right from WEAKEST to STRONGEST reference influence. "
                  "For img2img that means the strength number DECREASES left to right, because "
                  "strength is inverted." if method == "img2img" else
                  "Columns run left to right from weakest to strongest reference influence."),
        )

    # 4. multi-seed diversity -------------------------------------------------
    cells = []
    row_legend = []
    for method in COMPARISON_METHODS:
        strength = None if method == "text-only" else LEVEL_VALUES[method]["medium"]
        for condition in SWEEP_CONDITIONS:
            row_legend.append(f"row {len(row_legend) + 1} = {method} / {condition}")
            for seed in SEEDS:
                cells.append((f"{method}/{condition}/{seed}",
                              find(rows, method, condition, seed, strength)))
    # 148 px rather than the 192 px used elsewhere: this sheet carries 48 cells and
    # overran the 300 KB evidence limit at both 192 and 160. Diversity across seeds
    # is judged from overall composition and colour, which survives the reduction.
    builder.build(
        "multiseed-diversity.jpg", cells, columns=len(SEEDS), thumb=148,
        title="Multi-seed diversity at the medium level, 512x512",
        row_legend=row_legend,
        column_legend=[f"column {i + 1} = seed {s}" for i, s in enumerate(SEEDS)],
        note="This is what makes `diversity_across_seeds` scoreable for the first time. Its "
             "limitation is stated rather than glossed: it shows the three FROZEN seeds "
             "(42, 1337, 2026), not a random sample of the seed space.",
    )

    # 5 & 6. the two stress conditions ---------------------------------------
    for condition, name, title in (
        ("C5", "conflict-text-vs-reference.jpg",
         "C5 conflict: a figurative ukiyo-e reference against a minimal-geometric prompt"),
        ("C6", "difficult-reference-artefacts.jpg",
         "C6 difficult reference: frame, typography and landscape orientation"),
    ):
        methods = ("img2img", "ip-adapter")
        levels = ("weak", "medium", "strong")
        cells = [
            (f"{method}/{level}",
             find(rows, method, condition, PRIMARY_SEED, LEVEL_VALUES[method][level]))
            for method in methods
            for level in levels
        ]
        builder.build(
            name, cells, columns=len(levels), thumb=256, title=title,
            row_legend=[f"row {i + 1} = {m}" for i, m in enumerate(methods)],
            column_legend=[f"column {i + 1} = {lv}" for i, lv in enumerate(levels)],
            note=f"{CONDITIONS[condition].purpose}. Reference "
                 f"{CONDITIONS[condition].reference_id}: "
                 f"{REFERENCES[CONDITIONS[condition].reference_id].category}. "
                 "Prompt loss as influence rises is the measurement here, not a defect.",
        )

    # 7. the deck format ------------------------------------------------------
    methods = ("img2img", "ip-adapter")
    cells = [
        (f"{method}/{condition}",
         find(rows, method, condition, PRIMARY_SEED, LEVEL_VALUES[method]["medium"],
              width=512, height=1536))
        for method in methods
        for condition in DECK_CONDITIONS
    ]
    builder.build(
        "deck-format-512x1536.jpg", cells, columns=len(DECK_CONDITIONS), thumb=256,
        title="EXP-013 deck format 512x1536 at the medium level, seed 42",
        row_legend=[f"row {i + 1} = {m}" for i, m in enumerate(methods)],
        column_legend=[f"column {i + 1} = {c}" for i, c in enumerate(DECK_CONDITIONS)],
        note="img2img must crop each reference to 1:3 and lose the discarded area (R1 keeps "
             "~49 %, R2 100 %, R4 100 %); IP-Adapter passes the reference through a 224 px CLIP "
             "crop regardless of output geometry. Look here for repeated elements and vertical "
             "stretching, the open M3 observation.",
    )
    # 8. copy-risk pairs ------------------------------------------------------
    build_copy_risk_sheet(rows, builder)
    return builder


def load_similarity_rows() -> list[dict]:
    import csv

    rows: list[dict] = []
    directory = EVIDENCE / "EXP-014"
    if not directory.exists():
        return rows
    for path in sorted(directory.glob("similarity-*.csv")):
        with open(path, encoding="utf-8", newline="") as fh:
            rows.extend(list(csv.DictReader(fh)))
    return rows


def build_copy_risk_sheet(rows: list[dict], builder: SheetBuilder, limit: int = 8) -> None:
    """Reference beside output, closest perceptual match first.

    dHash distance is a COARSE NEAR-COPY FLAG ONLY - not a measure of style,
    quality, or influence strength. A near-copy is flagged and KEPT, never
    deleted: an output that reproduces its reference is a first-class RQ11
    finding, and this sheet exists so a human can judge whether it actually is
    one.
    """
    similarity = load_similarity_rows()
    if not similarity:
        print("  copy-risk-pairs.jpg: SKIPPED - no Phase-2 similarity rows yet")
        builder.reports.append({
            "name": "copy-risk-pairs.jpg", "built": False, "missing": [], "cells": 0,
            "title": "Reference beside its closest output by perceptual hash",
            "row_legend": ["not built"], "column_legend": ["not built"],
            "note": "Requires the Phase-2 indicators; run scripts/evaluate_similarity.py first.",
        })
        return

    by_hash = {r["output_sha256"]: r for r in rows}
    scored = []
    for row in similarity:
        if not row.get("reference_id") or row.get("status") != "ok":
            continue
        try:
            distance = int(row["dhash_distance_to_reference"])
        except (TypeError, ValueError):
            continue
        generation = by_hash.get(row["output_sha256"])
        if generation:
            scored.append((distance, row, generation))
    scored.sort(key=lambda item: item[0])
    closest = scored[:limit]

    cells = []
    row_legend = []
    for position, (distance, sim_row, generation) in enumerate(closest, start=1):
        reference = REPO / REFERENCES[sim_row["reference_id"]].repo_path
        cells.append((f"{sim_row['reference_id']} reference", reference))
        cells.append((f"{sim_row['reference_id']} output", REPO / generation["output_path"]))
        row_legend.append(
            f"row {position} = {sim_row['reference_id']} vs {sim_row['method']} "
            f"{sim_row['condition_id']} {sim_row['influence_level']} "
            f"({sim_row['strength_value']}) seed {sim_row['seed']} - **dHash distance "
            f"{distance}**{' - AT OR BELOW THE COPY-RISK THRESHOLD OF 6' if distance <= 6 else ''}"
        )

    builder.build(
        "copy-risk-pairs.jpg", cells, columns=2, thumb=256,
        title=f"The {len(closest)} outputs perceptually closest to their reference",
        row_legend=row_legend,
        column_legend=["column 1 = the reference image", "column 2 = the generated output"],
        note="Ordered by ascending dHash distance, closest first. dHash is a COARSE NEAR-COPY "
             "FLAG ONLY - not a measure of style, quality, or influence strength, and a low "
             "distance is a candidate for human judgement rather than a verdict. Near-copies "
             "are flagged and kept, never deleted: reproducing the reference is a first-class "
             "RQ11 finding. Score these under `originality` and `copy_or_overfitting_risk`.",
    )


def write_legend(builder: SheetBuilder) -> Path:
    lines = [
        "# Prototype 2 contact sheets - grid legend",
        "",
        "Every sheet below is a plain grid with no burnt-in labels, so this file is how a",
        "cell is identified. Rows fill left to right, top to bottom.",
        "",
        "**Two reading rules that apply throughout:**",
        "",
        "- **img2img `strength` is inverted** - a LOWER number means a STRONGER reference.",
        "  Sweep columns are ordered by ascending reference influence, so the img2img",
        "  strength numbers descend from left to right.",
        "- **The shared level names are an assumption under test, not a calibrated",
        "  equivalence.** img2img `strength=0.65` and IP-Adapter `scale=0.55` are both",
        "  labelled *medium*; nothing establishes that they exert comparable influence.",
        "",
        "No sheet carries a quality judgement. Scoring is the reviewer's, on the blank form.",
        "",
    ]
    for report in builder.reports:
        lines += [f"## `{report['name']}`", "", f"**{report['title']}**", ""]
        if not report["built"]:
            lines += ["> NOT BUILT - no cells were available.", ""]
        else:
            lines.append(f"{report['columns']} columns · {report['cells']} cells · "
                         f"{report['size_kb']} KB")
            lines.append("")
        lines.append(report["note"])
        lines += ["", "**Rows**", ""]
        lines += [f"- {item}" for item in report["row_legend"]]
        lines += ["", "**Columns**", ""]
        lines += [f"- {item}" for item in report["column_legend"]]
        if report["missing"]:
            lines += [
                "",
                f"**Missing cells ({len(report['missing'])}) - omitted from the grid, so cells "
                "after them shift position:**",
                "",
            ]
            lines += [f"- `{item}`" for item in report["missing"]]
        lines.append("")

    path = OUT_DIR / "contact-sheets.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    rows = load_rows()
    if not rows:
        print("no successful generation rows found - run the Phase-1 experiments first",
              file=sys.stderr)
        return 1
    print(f"{len(rows)} successful generation rows\n")
    builder = build_all(rows)
    legend = write_legend(builder)
    print(f"\nlegend: {legend}")

    oversized = [r for r in builder.reports if r.get("size_kb", 0) > 300]
    for report in oversized:
        print(f"  NOTE: {report['name']} is {report['size_kb']} KB, above the 300 KB guideline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
