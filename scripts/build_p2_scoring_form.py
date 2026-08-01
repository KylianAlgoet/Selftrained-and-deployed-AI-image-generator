"""Build the Prototype 2 rubric scoring form for the human-review gate.

Qualitative evaluation is the student's own research judgement (learning outcomes
D1/D4/D6), so this script never writes, estimates, suggests, or infers a score,
and it never names a method. It emits empty cells and the material needed to fill
them in.

Granularity follows how Kylian ACTUALLY reviewed in M3: aggregate rows at
(method x influence level x resolution). A per-unit inventory is emitted
alongside, with cells reading "not individually scored" unless they are genuinely
filled in - because presenting one aggregate judgement as dozens of independent
judgements would misrepresent the review.

Two dimensions are new in this milestone:

  * `reference_influence` is scoreable FOR THE FIRST TIME. Every rubric to date
    recorded it as N/A because no reference mechanism existed.
  * `copy_or_overfitting_risk` is added, because RQ11 and the near-copy flag both
    need it recorded rather than inferred from the dHash number.

Emits into docs/evidence/EXP-015-scoring/:
  - rubric.md               the 10 dimensions and their 1-5 anchors
  - scoring-form.md / .csv  blank aggregate rows plus the per-unit inventory
  - failure-mode-probe.md   the carried-over M3 failure checklist

Run:
    .venv/Scripts/python.exe scripts/build_p2_scoring_form.py
"""

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.evaluation import prompt_kit  # noqa: E402
from ml.inference.reference_schema import (  # noqa: E402
    CONDITIONS,
    METHODS,
    REFERENCES,
    STATUS_OK,
    read_jsonl,
)

EVIDENCE = REPO / "docs" / "evidence"
OUT_DIR = EVIDENCE / "EXP-015-scoring"
SHEETS = EVIDENCE / "prototype-2"

SOURCE_EXPERIMENTS = ("EXP-008", "EXP-008b", "EXP-009", "EXP-009b", "EXP-010",
                      "EXP-011", "EXP-012", "EXP-013")

# The 9 dimensions from docs/05-experiment-methodology.md, plus the M4 addition.
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
    ("copy_or_overfitting_risk", "reproduces the reference", "no trace of copying"),
]

NEW_IN_P2 = {"reference_influence", "copy_or_overfitting_risk"}

FAILURE_PROBES: list[tuple[str, str]] = [
    ("repeated_elements", "duplicated motifs, especially at 512x1536 (the open M3 observation)"),
    ("vertical_stretching", "subjects stretched to fill the 1:3 deck format"),
    ("physical_deck_mockup", "renders a photo of a skateboard instead of the artwork "
                             "(the failure flagged in EXP-005 direct-1x1)"),
    ("unwanted_frame", "a border or mount transferred from a framed reference scan"),
    ("pseudo_text", "invented lettering transferred from a text-dominated reference"),
    ("background_transfer", "the reference's background carried over wholesale"),
]


def load_approved_scores() -> dict[tuple, dict]:
    """Kylian's approved aggregate scores, keyed to the form's own row identity.

    `human-scores.csv` is the authoritative record. This script only joins it onto
    the inventory of what was actually generated; it never derives, averages, or
    infers a score. An empty cell there means NOT SCORED and stays empty here -
    it is never back-filled from another row, another resolution, or another
    milestone.
    """
    path = OUT_DIR / "human-scores.csv"
    if not path.exists():
        return {}
    approved: dict[tuple, dict] = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            key = (row["method"], row["influence_level"],
                   row["strength_value"].strip(), row["resolution"])
            approved[key] = row
    return approved


def unit_key(unit: dict) -> tuple:
    return (unit["method"], unit["influence_level"],
            str(unit["strength_value"]).strip(), unit["resolution"])


def load_failure_observations() -> list[dict]:
    """Kylian's approved failure-mode observations, recorded verbatim."""
    path = OUT_DIR / "failure-mode-observations.csv"
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_rows() -> list[dict]:
    rows: list[dict] = []
    for exp_id in SOURCE_EXPERIMENTS:
        directory = EVIDENCE / exp_id
        if not directory.exists():
            continue
        for path in sorted(directory.glob("results-*.jsonl")):
            rows.extend(read_jsonl(path))
    return rows


def aggregate_units(rows: list[dict]) -> list[dict]:
    """One row per (method, influence level, strength, resolution) - the level at
    which the review is actually performed."""
    seen: dict[tuple, dict] = {}
    for row in rows:
        if row["status"] != STATUS_OK:
            continue
        key = (row["method"], row["influence_level"], str(row.get("strength_value", "")),
               int(row["width"]), int(row["height"]))
        entry = seen.setdefault(key, {
            "method": row["method"],
            "influence_level": row["influence_level"],
            "strength_param": row.get("strength_param_name", ""),
            "strength_value": row.get("strength_value", ""),
            "resolution": f"{row['width']}x{row['height']}",
            "conditions": set(),
            "seeds": set(),
            "experiments": set(),
            "images": 0,
        })
        entry["conditions"].add(row["condition_id"])
        entry["seeds"].add(str(row["seed"]))
        entry["experiments"].add(row["exp_id"])
        entry["images"] += 1
    units = []
    for key in sorted(seen):
        entry = seen[key]
        entry["conditions"] = ",".join(sorted(entry["conditions"]))
        entry["seeds"] = ",".join(sorted(entry["seeds"], key=int))
        entry["experiments"] = ",".join(sorted(entry["experiments"]))
        units.append(entry)
    return units


def write_rubric() -> Path:
    lines = [
        "# Prototype 2 evaluation rubric (1-5 per dimension)",
        "",
        "Nine dimensions from `docs/05-experiment-methodology.md` plus one M4 addition.",
        "Scores are the student's own research judgement; nothing here is estimated,",
        "suggested, or filled in by the assistant.",
        "",
        "| dimension | 1 | 5 | note |",
        "|---|---|---|---|",
    ]
    for name, low, high in DIMENSIONS:
        if name == "reference_influence":
            note = "**scoreable for the first time** - every rubric to date recorded N/A"
        elif name == "copy_or_overfitting_risk":
            note = "**new in M4** - RQ11 and the near-copy flag both need it recorded"
        else:
            note = "unchanged from Prototype 1"
        lines.append(f"| {name} | {low} | {high} | {note} |")

    lines += [
        "",
        "## The four axes, kept separate",
        "",
        "These are deliberately never collapsed into one score, and the automatic",
        "indicators never replace the human judgement:",
        "",
        "| axis | decided by | supported, never replaced, by |",
        "|---|---|---|",
        "| content preservation | `reference_influence` | `dhash_distance_to_reference`, a coarse near-copy flag only |",
        "| style influence | `style_consistency` | nothing - no automatic proxy is claimed |",
        "| prompt adherence | `prompt_adherence`; C5 forces the trade-off open | - |",
        "| copy risk | `originality` + `copy_or_overfitting_risk` | `dhash <= 6` flags candidates for the copy-risk sheet |",
        "",
        "`overall_reference_similarity` (CLIP cosine) is a **descriptive indicator across all",
        "four and attributable to none of them individually.** It entangles subject,",
        "composition, semantics, colour and style, so it is not a style score. It is also",
        "computed with the same CLIP family IP-Adapter conditions on, which makes it",
        "descriptive *within* a method rather than a neutral referee *between* methods.",
        "**The human rubric is the decision authority.**",
        "",
        "## How to score",
        "",
        "1. Read `docs/evidence/prototype-2/contact-sheets.md` first - the sheets carry no",
        "   burnt-in labels, so that file is how a cell is identified.",
        "2. `method-comparison-medium-seed42.jpg` - the like-for-like comparison at one level.",
        "3. `sweep-img2img-seed42.jpg` and `sweep-ipadapter-seed42.jpg` - is influence",
        "   *controllable*? Columns run weakest to strongest reference influence. **For",
        "   img2img the strength number DECREASES left to right, because strength is inverted.**",
        "4. `multiseed-diversity.jpg` - the only sheet that can answer `diversity_across_seeds`.",
        "5. `conflict-text-vs-reference.jpg` (C5) - when reference and prompt disagree, which",
        "   wins as influence rises? Prompt loss here is the measurement, not a defect.",
        "6. `difficult-reference-artefacts.jpg` (C6) and `copy-risk-pairs.jpg`.",
        "7. `deck-format-512x1536.jpg` - does control survive the production geometry?",
        "8. Fill in `scoring-form.md` at aggregate level and the failure probe checklist.",
        "",
        "**A note on the shared level names.** `medium` means `strength=0.65` for img2img and",
        "`scale=0.55` for IP-Adapter. That mapping is an assumption under test, not a",
        "calibrated equivalence - nothing establishes the two exert comparable influence.",
        "Score what you see rather than assuming the labels are matched.",
        "",
        "Leave a cell blank rather than guessing. A blank cell is recorded as",
        "\"not scored\"; it is never back-filled.",
        "",
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "rubric.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_forms(units: list[dict]) -> tuple[Path, Path]:
    names = [name for name, _, _ in DIMENSIONS]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    approved = load_approved_scores()
    reviewed = bool(approved)

    def cells_for(unit: dict) -> tuple[dict[str, str], str]:
        """Scores for one row. Absent row or empty cell -> empty string, always."""
        record = approved.get(unit_key(unit))
        if record is None:
            return {name: "" for name in names}, ""
        return ({name: (record.get(name) or "").strip() for name in names},
                (record.get("note") or "").strip())

    csv_path = OUT_DIR / "scoring-form.csv"
    fieldnames = ["method", "influence_level", "strength_param", "strength_value",
                  "resolution", "conditions", "seeds", "experiments", "images", *names, "notes"]
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for unit in units:
            scores, note = cells_for(unit)
            writer.writerow({
                **{k: unit[k] for k in ("method", "influence_level", "strength_param",
                                        "strength_value", "resolution", "conditions",
                                        "seeds", "experiments", "images")},
                **scores,
                "notes": note,
            })

    unscored = sum(
        1 for unit in units for value in cells_for(unit)[0].values() if value == ""
    )

    if reviewed:
        lines = [
            "# Prototype 2 scoring form (SCORED by Kylian, 2026-08-01)",
            "",
            f"Frozen kit fingerprint: `{prompt_kit.kit_fingerprint()}`",
            "",
            "Rows are at **aggregate (method x influence level x resolution)** granularity, which",
            "is the granularity the review was actually performed at. Scale: 1 = worst, 5 = best.",
            "",
            "The authoritative record is [`human-scores.csv`](human-scores.csv); this table is",
            "generated from it and joined onto the inventory of what was actually generated. No",
            "score here is derived, averaged, or inferred.",
            "",
            f"**An empty cell means NOT SCORED and is never back-filled** ({unscored} such cells).",
            "It is not a zero, and it is never carried over from another row, another resolution,",
            "or another milestone. In particular:",
            "",
            "- `diversity_across_seeds` was scored only where the multi-seed sheet supported it.",
            "- `reference_influence` and `copy_or_overfitting_risk` are blank for **text-only**,",
            "  which uses no reference image at all.",
            "- **text-only at 512x1536 is entirely unscored:** it was not visually rescored from",
            "  the M4 contact sheets, and no M3 value has been substituted for it.",
            "",
            "`reference_influence` is scored here for the first time in the project.",
            "",
        ]
    else:
        lines = [
            "# Prototype 2 scoring form (BLANK - to be filled in by Kylian)",
            "",
            f"Frozen kit fingerprint: `{prompt_kit.kit_fingerprint()}`",
            "",
            "Rows are at **aggregate (method x influence level x resolution)** granularity, which",
            "is how the M3 review was actually performed. Scale: 1 = worst, 5 = best.",
            "",
            "Every score cell is intentionally empty. See [`rubric.md`](rubric.md) for the 1-5",
            "anchors and the recommended order of review, and",
            "[`failure-mode-probe.md`](failure-mode-probe.md) for the checklist that goes with it.",
            "",
            "`reference_influence` is scoreable here for the first time in the project.",
            "",
        ]

    for resolution in sorted({u["resolution"] for u in units}, key=lambda r: (len(r), r)):
        lines += [f"## {resolution}", ""]
        lines.append("| method | level | param | value | conditions | seeds | n | "
                     + " | ".join(names) + " | notes |")
        lines.append("|" + "---|" * (len(names) + 8))
        for unit in [u for u in units if u["resolution"] == resolution]:
            scores, note = cells_for(unit)
            lines.append(
                f"| {unit['method']} | {unit['influence_level']} | {unit['strength_param'] or '-'} | "
                f"{unit['strength_value'] if unit['strength_value'] != '' else '-'} | "
                f"{unit['conditions']} | {unit['seeds']} | {unit['images']} | "
                + " | ".join(scores[name] for name in names) + f" | {note} |"
            )
        lines.append("")

    lines += [
        "## Conditions referenced above",
        "",
        "| condition | reference | prompt | purpose |",
        "|---|---|---|---|",
    ]
    for condition in CONDITIONS.values():
        lines.append(f"| {condition.id} | {condition.reference_id} "
                     f"({REFERENCES[condition.reference_id].category}) | "
                     f"{condition.prompt_id} | {condition.purpose} |")

    lines += [
        "",
        "## Methods referenced above",
        "",
        "| method | native parameter | direction |",
        "|---|---|---|",
    ]
    for spec in METHODS.values():
        direction = ("n/a - no reference" if not spec.strength_param_name
                     else "INVERTED: lower value = stronger reference"
                     if spec.strength_inverted else "higher value = stronger reference")
        lines.append(f"| {spec.label} | {spec.strength_param_name or '-'} | {direction} |")

    lines += [
        "",
        "## Where the images are",
        "",
        "Full-resolution PNGs are git-ignored under `outputs/EXP-###/`. The committed contact",
        "sheets and their grid legend are in `docs/evidence/prototype-2/`.",
        "",
    ]

    md_path = OUT_DIR / "scoring-form.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path, csv_path


def write_failure_probe() -> Path:
    observations = load_failure_observations()
    scored = bool(observations)
    probe_names = [name for name, _ in FAILURE_PROBES]

    def cells(section: str, method: str, unit: str) -> tuple[list[str], str]:
        for row in observations:
            if (row["section"], row["method"], row["unit"]) == (section, method, unit):
                return ([(row.get(name) or "").strip() for name in probe_names],
                        (row.get("note") or "").strip())
        return (["" for _ in probe_names], "")

    title = ("# Prototype 2 failure-mode probe (OBSERVED by Kylian, 2026-08-01)" if scored
             else "# Prototype 2 failure-mode probe (BLANK - to be filled in by Kylian)")
    lines = [
        title,
        "",
        "Carried over from M3 and M2. For each method and level, does reference conditioning",
        "**reduce**, **leave unchanged**, or **worsen** each failure mode? One of",
        "`reduced` / `unchanged` / `worse` / `not observed`; a blank means it could not be judged.",
        "",
        "This is a separate instrument from the rubric on purpose: these are presence/absence",
        "observations about specific artefacts, not quality judgements on a 1-5 scale.",
        "",
    ]
    if scored:
        lines += [
            "Recorded verbatim from the approved review. The authoritative record is",
            "[`failure-mode-observations.csv`](failure-mode-observations.csv); nothing here is",
            "inferred, and `not observed` is recorded as itself rather than as `reduced`.",
            "",
        ]
    lines += [
        "## What each probe means",
        "",
    ]
    for name, description in FAILURE_PROBES:
        lines.append(f"- **`{name}`** - {description}")

    lines += [
        "",
        "## C6, the difficult reference (`difficult-reference-artefacts.jpg`)",
        "",
        "R5 is a landscape, framed, text-dominated WPA poster scan. **R1 shares the frame and",
        "typography properties**, so C1 is worth checking for the same artefacts - R5 is the",
        "harder case because it adds landscape orientation, not because it is the only framed",
        "or text-bearing reference.",
        "",
        "| method | level | " + " | ".join(probe_names) + " | notes |",
        "|" + "---|" * (len(FAILURE_PROBES) + 3),
    ]
    for method in ("img2img", "ip-adapter"):
        for level in ("weak", "medium", "strong"):
            values, note = cells("C6", method, level)
            lines.append(f"| {method} | {level} | " + " | ".join(values) + f" | {note} |")

    lines += [
        "",
        "## EXP-013, the deck format (`deck-format-512x1536.jpg`)",
        "",
        "`repeated_elements` and `vertical_stretching` are the open M3 observation at 512x1536;",
        "this is the first evidence bearing on whether reference conditioning affects them.",
        "",
        "| method | condition | " + " | ".join(probe_names) + " | notes |",
        "|" + "---|" * (len(FAILURE_PROBES) + 3),
    ]
    for method in ("img2img", "ip-adapter"):
        for condition in ("C1", "C2", "C4"):
            values, note = cells("EXP-013", method, condition)
            lines.append(f"| {method} | {condition} | " + " | ".join(values) + f" | {note} |")

    lines += [
        "",
        "## Relation to the open dataset findings",
        "",
        "Whatever is observed here is **evidence**, not the mitigation decision. The dataset",
        "mitigation for framed and text-heavy source material (crop pass vs negative prompting)",
        "stays in **Prototype 4 / M6**, where training evidence will exist.",
        "",
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "failure-mode-probe.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    rows = load_rows()
    if not rows:
        print("no generation results found - run scripts/run_reference_conditioning.py first",
              file=sys.stderr)
        return 1
    units = aggregate_units(rows)
    if not units:
        print("no successful runs to score", file=sys.stderr)
        return 1

    rubric = write_rubric()
    md_path, csv_path = write_forms(units)
    probe = write_failure_probe()

    print(f"rubric ............ {rubric}")
    print(f"scoring form ...... {md_path}")
    print(f"scoring csv ....... {csv_path}")
    print(f"failure probe ..... {probe}")
    print(f"\n{len(units)} aggregate scoring units over {sum(u['images'] for u in units)} images")
    approved = load_approved_scores()
    if approved:
        matched = sum(1 for u in units if unit_key(u) in approved)
        print(f"approved score rows joined: {matched}/{len(units)}")
        unmatched = [unit_key(u) for u in units if unit_key(u) not in approved]
        for key in unmatched:
            print(f"  NOT SCORED (left blank): {key}")
        orphans = set(approved) - {unit_key(u) for u in units}
        for key in sorted(orphans):
            print(f"  WARNING approved row matches no generated unit: {key}")
    else:
        print("All score cells are blank by design. Scores are the student's judgement,")
        print("and no method is named until they are supplied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
