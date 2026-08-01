"""Prototype 2 measurement analysis: process isolation, monotonicity, combined summary.

Everything here is computed from the recorded data and reported as it comes out,
including when it comes out negative. Nothing in this script selects a method,
scores an image, or writes a conclusion - those belong to the human-review gate.

Three questions, each answered from data rather than asserted in prose:

1. **Was the shared-process comparison legitimate?** Influence levels share one OS
   process per (method, resolution, tier). The clean-process spot checks re-ran
   weak/medium/strong at one fixed cell, each in its own process. If a clean
   `peak_vram_allocated_mb` differs from its shared-process counterpart by more
   than the PRE-DECLARED 2 %, the shared-process comparison is REJECTED and that
   method must be re-run one level per process. The result is recorded either
   way, including when it confirms the shared process was fine.

2. **Is reference influence monotone?** Does median overall reference-image
   similarity rise as the shared influence level rises? A condition without at
   least two ordered levels is reported as unanswerable, never as a guess.

3. **What did the lower-bound diagnostic find?** Whether IP-Adapter at scale 0.0
   reproduces the text-only baseline hash, and whether that baseline reproduces
   the Prototype 1 EXP-002 hashes. **A hash mismatch alone does not fail the
   lower-bound controllability condition** - loading IP-Adapter replaces
   attention processors and may alter the execution graph even at zero scale.

Run:
    .venv/Scripts/python.exe scripts/build_p2_analysis.py
"""

import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.inference.reference_schema import (  # noqa: E402
    COPY_RISK_MAX_DHASH_DISTANCE,
    LEVEL_VALUES,
    MONOTONICITY_LEVEL_ORDER,
    PHYSICAL_VRAM_MIB,
    SPOT_CHECK_TOLERANCE_FRACTION,
    STATUS_OK,
    monotonicity_by_condition,
    read_jsonl,
    render_summary_markdown,
    spot_check_within_tolerance,
    summarize,
    write_csv,
)

EVIDENCE = REPO / "docs" / "evidence"
OUT_DIR = EVIDENCE / "prototype-2"

SOURCE_EXPERIMENTS = ("EXP-008", "EXP-008b", "EXP-009", "EXP-009b", "EXP-010",
                      "EXP-011", "EXP-012", "EXP-013")
SPOT_CHECK_PAIRS = (("EXP-008", "EXP-008b", "img2img"), ("EXP-009", "EXP-009b", "ip-adapter"))
SPOT_CHECK_CONDITION = "C1"
SPOT_CHECK_SEED = 42


def load_rows(experiments=SOURCE_EXPERIMENTS) -> list[dict]:
    rows: list[dict] = []
    for exp_id in experiments:
        directory = EVIDENCE / exp_id
        if not directory.exists():
            continue
        for path in sorted(directory.glob("results-*.jsonl")):
            rows.extend(read_jsonl(path))
    return rows


def _find(rows, exp_id, method, strength, condition=SPOT_CHECK_CONDITION, seed=SPOT_CHECK_SEED):
    for row in rows:
        if (row.get("exp_id") == exp_id and row["method"] == method
                and row["condition_id"] == condition and int(row["seed"]) == seed
                and row["status"] == STATUS_OK):
            try:
                if abs(float(row["strength_value"]) - strength) < 1e-9:
                    return row
            except (TypeError, ValueError):
                continue
    return None


# --- 1. process isolation ----------------------------------------------------


def process_isolation(rows: list[dict]) -> tuple[str, bool]:
    lines = [
        "# Prototype 2 process-isolation check",
        "",
        "A fresh OS process is used per **method x adapter variant x output resolution x",
        "memory tier**. Influence levels deliberately **share** a process inside one such",
        "combination, because tensor geometry does not change across levels and reloading",
        "SD 1.5 per level would multiply runtime for no measurement gain.",
        "",
        "That sharing is declared rather than hidden, and it is checked rather than trusted.",
        "This carries three obligations:",
        "",
        "- `peak_vram_allocated_mb` is **per run** and is the level-to-level figure;",
        "- `peak_vram_reserved_mb` and `peak_device_used_mb` are **process-level high-water",
        "  marks** and are never compared between levels sharing a process (cross-*method*",
        "  comparison stays valid, because each method has its own fresh process);",
        "- the spot check below must pass before the shared-process comparison is accepted.",
        "",
        f"**Tolerance: {SPOT_CHECK_TOLERANCE_FRACTION:.0%}, pre-declared in",
        "`ml/inference/reference_schema.py` before any measurement, so it cannot be tuned",
        "to the result.**",
        "",
        f"Spot-check cell: condition {SPOT_CHECK_CONDITION}, seed {SPOT_CHECK_SEED}, 512x512,",
        "tier 0. Each clean run had its own OS process; each shared run came from the",
        "method's sweep process.",
        "",
        "| method | level | value | shared-process alloc MiB | clean-process alloc MiB | delta | delta % | within tolerance |",
        "|---|---|---|---|---|---|---|---|",
    ]

    failures = 0
    missing = 0
    checked = 0
    for shared_exp, clean_exp, method in SPOT_CHECK_PAIRS:
        for level in ("weak", "medium", "strong"):
            value = LEVEL_VALUES[method][level]
            shared = _find(rows, shared_exp, method, value)
            clean = _find(rows, clean_exp, method, value)
            if shared is None or clean is None:
                lines.append(f"| {method} | {level} | {value} | "
                             f"{'not measured' if shared is None else shared['peak_vram_allocated_mb']} | "
                             f"{'not measured' if clean is None else clean['peak_vram_allocated_mb']} | "
                             "- | - | **not measured** |")
                # A missing pair is an ABSENT check, not a failed one. Conflating
                # the two would report a tolerance breach that never happened.
                missing += 1
                continue
            shared_mb = float(shared["peak_vram_allocated_mb"])
            clean_mb = float(clean["peak_vram_allocated_mb"])
            within = spot_check_within_tolerance(shared_mb, clean_mb)
            delta = shared_mb - clean_mb
            pct = delta / clean_mb * 100
            failures += 0 if within else 1
            checked += 1
            lines.append(f"| {method} | {level} | {value} | {shared_mb:.2f} | {clean_mb:.2f} | "
                         f"{delta:+.2f} | {pct:+.3f} % | {'yes' if within else '**NO**'} |")

    lines += ["", "## Verdict", ""]
    if missing:
        lines += [
            f"**{missing} of {checked + missing} pairs could not be checked** because one or both",
            "of their runs is absent from the results. That is an **absent check, not a failed",
            "one** - nothing about those pairs exceeded the tolerance, because nothing about them",
            "was measured. They are reported as `not measured` above.",
            "",
        ]
    if checked == 0:
        lines += ["**Not established.** No comparable pair was found, so the shared-process",
                  "comparison is neither accepted nor rejected here.", ""]
    elif failures == 0 and missing:
        lines += [
            f"**Partially established.** All {checked} pairs that could be checked agree within the",
            f"pre-declared {SPOT_CHECK_TOLERANCE_FRACTION:.0%} tolerance. The shared-process comparison is accepted",
            "for the method(s) fully covered above and remains **unverified** for the rest until",
            "their spot-check runs exist.",
            "",
        ]
    elif failures == 0:
        lines += [
            f"**The shared-process comparison is ACCEPTED.** All {checked} spot-check pairs agree",
            f"within the pre-declared {SPOT_CHECK_TOLERANCE_FRACTION:.0%} tolerance, so sharing a process",
            "across influence levels did not distort `peak_vram_allocated_mb`. No method needs",
            "re-running one level per process.",
            "",
            "This is a confirmation, and it is recorded as one: the check was worth running",
            "precisely because it could have come out the other way, as EXP-005's allocator",
            "contamination did one milestone earlier.",
            "",
        ]
    else:
        lines += [
            "**The shared-process comparison is REJECTED for the affected method(s).**",
            f"{failures} of {checked} checked pairs exceeded the pre-declared",
            f"{SPOT_CHECK_TOLERANCE_FRACTION:.0%} tolerance. Per the plan, that method must be re-run one level per",
            "process before its level-to-level figures are used. This is recorded as a finding,",
            "not worked around.",
            "",
        ]

    lines += [
        "## Process inventory",
        "",
        "Every `process_config_key` present in the results, with the runs it produced.",
        "",
        "| process_config_key | runs | ok | failed | max peak alloc MiB | max peak reserved MiB (process-level) |",
        "|---|---|---|---|---|---|",
    ]
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row.get("process_config_key", "(none)"), []).append(row)
    for key in sorted(groups):
        group = groups[key]
        ok = [r for r in group if r["status"] == STATUS_OK]
        alloc = [float(r["peak_vram_allocated_mb"]) for r in ok
                 if _is_number(r["peak_vram_allocated_mb"])]
        reserved = [float(r["peak_vram_reserved_mb"]) for r in ok
                    if _is_number(r["peak_vram_reserved_mb"])]
        lines.append(f"| `{key}` | {len(group)} | {len(ok)} | {len(group) - len(ok)} | "
                     f"{max(alloc):.2f} | {max(reserved):.2f} |" if alloc and reserved
                     else f"| `{key}` | {len(group)} | {len(ok)} | {len(group) - len(ok)} | "
                          "not measured | not measured |")

    lines += [
        "",
        "Note that one `process_config_key` value can be produced by more than one OS process:",
        "the spot-check runs share a key with their sweep counterparts by construction, which",
        "is exactly what makes them comparable.",
        "",
    ]
    return "\n".join(lines), checked > 0 and failures == 0 and missing == 0


def _is_number(value) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


# --- 2. monotonicity ---------------------------------------------------------


def monotonicity(similarity_rows: list[dict]) -> str:
    lines = [
        "# Prototype 2 monotonicity check",
        "",
        "**Question.** Does the median `overall_reference_similarity` increase as the shared",
        "influence level rises? This is controllability condition 3 of four, and the plan",
        "sets the bar at **at least 3 of the 4 style-matched conditions**.",
        "",
        "**What this number is.** Cosine similarity of CLIP ViT-H image embeddings between an",
        "output and its reference. It entangles subject, composition, semantics, colour and",
        "style, so it is an **overall reference-image similarity indicator, never a style",
        "score.** Style transfer is judged by the human `style_consistency` dimension.",
        "",
        "**Stated limitation.** The CLIP tower used here is the same family IP-Adapter",
        "conditions on, so this indicator is descriptive **within** a method and is not a",
        "neutral referee **between** methods. It orders the levels; the rubric decides.",
        "",
        f"Levels are ordered by ascending reference influence: {' < '.join(MONOTONICITY_LEVEL_ORDER)}.",
        "For img2img that is the **opposite** of ascending `strength`, which is inverted.",
        "",
    ]
    if not similarity_rows:
        lines += ["**Not computed.** No Phase-2 similarity rows exist yet; run",
                  "`scripts/evaluate_similarity.py` first. No value is estimated in the meantime.",
                  ""]
        return "\n".join(lines)

    methods = sorted({r["method"] for r in similarity_rows if r["method"] != "text-only"})
    lines += ["| method | condition | monotone? | median similarity by level |", "|---|---|---|---|"]
    summary: dict[str, tuple[int, int]] = {}
    for method in methods:
        result = monotonicity_by_condition(similarity_rows, method)
        true_count = sum(1 for v in result.values() if v is True)
        answerable = sum(1 for v in result.values() if v is not None)
        summary[method] = (true_count, answerable)
        for condition, verdict in sorted(result.items()):
            medians = _medians_by_level(similarity_rows, method, condition)
            shown = ", ".join(f"{lvl} {val:.4f}" for lvl, val in medians) or "-"
            label = {True: "yes", False: "no", None: "unanswerable"}[verdict]
            lines.append(f"| {method} | {condition} | {label} | {shown} |")

    lines += ["", "## Counts", "",
              "| method | conditions monotone | conditions answerable | bar (>= 3 of 4 style-matched) |",
              "|---|---|---|---|"]
    for method, (true_count, answerable) in summary.items():
        if answerable == 0:
            # A method run at one level only cannot be monotone or non-monotone.
            # Labelling that "not met" would report a failure it never had.
            met = "not applicable - single level measured, so monotonicity is untestable"
        else:
            met = "met" if true_count >= 3 else "not met"
        lines.append(f"| {method} | {true_count} | {answerable} | {met} |")

    lines += [
        "",
        "`unanswerable` means that condition had fewer than two ordered levels with usable",
        "values. It is reported as an absent answer rather than filled in.",
        "",
        "This check orders levels by an automatic indicator only. Whether the ordering is",
        "**visible and useful to a human** is controllability condition 4, and it is settled",
        "by the rubric at the review gate, not here.",
        "",
    ]
    return "\n".join(lines)


def copy_risk(similarity_rows: list[dict]) -> str:
    """Near-copy candidates, grouped so the pattern is visible rather than buried.

    dHash distance is a COARSE NEAR-COPY FLAG ONLY. A low distance marks an output
    for human judgement under `originality` and `copy_or_overfitting_risk`; it is
    not itself a verdict that copying occurred.
    """
    lines = [
        "# Prototype 2 copy-risk flags",
        "",
        f"Threshold: perceptual-hash (dHash) Hamming distance **<= {COPY_RISK_MAX_DHASH_DISTANCE}**, the",
        "project's existing `NEAR_DUPLICATE_MAX_DISTANCE`, reused unchanged.",
        "",
        "**What this is and is not.** dHash distance is model-free and coarse. It is a",
        "**near-copy flag only** - not a measure of style, quality, or influence strength, and",
        "not by itself a finding that copying occurred. A flagged output is a candidate for",
        "human judgement under `originality` and `copy_or_overfitting_risk`. Flagged outputs are",
        "**kept and surfaced, never deleted**: an output that reproduces its reference is a",
        "first-class RQ11 result.",
        "",
    ]
    flagged = []
    for row in similarity_rows:
        try:
            distance = int(row["dhash_distance_to_reference"])
        except (TypeError, ValueError):
            continue
        if distance <= COPY_RISK_MAX_DHASH_DISTANCE:
            flagged.append((distance, row))
    flagged.sort(key=lambda item: item[0])

    if not flagged:
        lines += ["**No output fell at or below the threshold.**", ""]
        return "\n".join(lines)

    lines += [
        f"## {len(flagged)} flagged output(s)",
        "",
        "| dHash | experiment | method | condition | reference | level | value | seed | geometry | CLIP similarity |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for distance, row in flagged:
        lines.append(
            f"| **{distance}** | {row['exp_id']} | {row['method']} | {row['condition_id']} | "
            f"{row['reference_id']} | {row['influence_level']} | {row['strength_value']} | "
            f"{row['seed']} | {row['width']}x{row['height']} | {row['overall_reference_similarity']} |"
        )

    # Where the flags concentrate is the actual finding, so it is computed rather
    # than left for a reader to notice.
    geometries = {f"{r['width']}x{r['height']}" for _, r in flagged}
    methods = {r["method"] for _, r in flagged}
    references = {r["reference_id"] for _, r in flagged}
    lines += [
        "",
        "## Where the flags concentrate",
        "",
        f"- geometries: {', '.join(sorted(geometries))}",
        f"- methods: {', '.join(sorted(methods))}",
        f"- references: {', '.join(sorted(references))}",
        "",
        "### Median dHash distance to the reference, img2img at the medium level",
        "",
        "| geometry | runs | median dHash | minimum |",
        "|---|---|---|---|",
    ]
    for width, height in ((512, 512), (512, 1536)):
        values = [
            int(r["dhash_distance_to_reference"])
            for r in similarity_rows
            if r["method"] == "img2img" and r["influence_level"] == "medium"
            and (int(r["width"]), int(r["height"])) == (width, height)
            and str(r["dhash_distance_to_reference"]).strip()
        ]
        if values:
            lines.append(f"| {width}x{height} | {len(values)} | {statistics.median(values):g} | {min(values)} |")

    lines += [
        "",
        "The same method at the same level behaves very differently at the two geometries. The",
        "mechanism is mechanical and stated as such: **img2img forces the reference into the",
        "output resolution**, so when a reference already matches the output aspect exactly - R2",
        "and R4 are natively 512x1536 and retain 100 % of their area at the deck format - nothing",
        "is cropped away and denoising at `strength=0.65` starts from an essentially intact copy.",
        "At 512x512 the same references are cropped to a third of their area first.",
        "",
        "**This concerns the production geometry**, so it is surfaced rather than filed as an",
        "edge case. Whether these outputs actually read as copies is a human judgement: see",
        "`copy-risk-pairs.jpg` and score them under `originality` and `copy_or_overfitting_risk`.",
        "No conclusion about method selection is drawn here.",
        "",
    ]
    return "\n".join(lines)


def _medians_by_level(rows, method, condition) -> list[tuple[str, float]]:
    by_level: dict[str, list[float]] = {}
    for row in rows:
        if row["method"] != method or row["condition_id"] != condition:
            continue
        try:
            by_level.setdefault(row["influence_level"], []).append(
                float(row["overall_reference_similarity"])
            )
        except (TypeError, ValueError):
            continue
    return [(level, statistics.median(by_level[level]))
            for level in MONOTONICITY_LEVEL_ORDER if by_level.get(level)]


# --- 3. the lower-bound diagnostic ------------------------------------------


def lower_bound_diagnostic(rows: list[dict]) -> str:
    lines = [
        "# EXP-010 lower-bound equivalence diagnostic",
        "",
        "**This is a diagnostic, and it is worded as one.** Controllability condition 1 says",
        "that at minimum influence the output should be equivalent to the text-only baseline.",
        "Equivalence is established in this order: exact `output_sha256` match, and if the",
        "hashes differ, documented pixel and perceptual similarity plus visual inspection.",
        "",
        "**Differing PNG hashes alone do not fail this condition.** Loading IP-Adapter replaces",
        "attention processors and may alter the execution graph even at scale 0.0. Exact",
        "equality is a strong positive result, never a promise.",
        "",
        "## Comparison A - IP-Adapter at scale 0.0 vs the text-only baseline",
        "",
        "| condition | seed | baseline sha256 | scale-0.0 sha256 | identical |",
        "|---|---|---|---|---|",
    ]
    # Height must be filtered too, not only width: EXP-010 also contains the
    # 512x1536 deck baseline, which is 512 wide and would otherwise overwrite the
    # 512x512 entry for the same prompt and seed.
    baseline = {(r["prompt_id"], int(r["seed"])): r for r in rows
                if r["method"] == "text-only" and r["exp_id"] == "EXP-010"
                and r["status"] == STATUS_OK
                and int(r["width"]) == 512 and int(r["height"]) == 512}
    zero = [r for r in rows if r["method"] == "ip-adapter" and r["exp_id"] == "EXP-010"
            and r["status"] == STATUS_OK and str(r.get("influence_level")) == "none"
            and int(r["height"]) == 512]

    matches = 0
    for row in sorted(zero, key=lambda r: (r["condition_id"], int(r["seed"]))):
        base = baseline.get((row["prompt_id"], int(row["seed"])))
        if base is None:
            lines.append(f"| {row['condition_id']} | {row['seed']} | not measured | "
                         f"`{row['output_sha256'][:16]}...` | cannot compare |")
            continue
        identical = base["output_sha256"] == row["output_sha256"]
        matches += identical
        lines.append(f"| {row['condition_id']} | {row['seed']} | `{base['output_sha256'][:16]}...` | "
                     f"`{row['output_sha256'][:16]}...` | {'**yes**' if identical else 'no'} |")

    total = len([r for r in zero if baseline.get((r["prompt_id"], int(r["seed"]))) is not None])
    lines += ["", f"**{matches} of {total} pairs are byte-identical.**", ""]
    if total and matches == total:
        lines += [
            "Every pair matched exactly. That is a strong positive result: at scale 0.0 the",
            "IP-Adapter cross-attention path contributes nothing, and the method's lower bound",
            "is the text-only baseline exactly rather than approximately.",
            "",
        ]
    elif total and matches == 0:
        lines += [
            "No pair matched. This is **not** a controllability failure on its own - see the",
            "note above. The likely cause is that replacing 16 of the UNet's 32 attention",
            "processors alters the execution graph even when the adapter contributes zero.",
            "The Phase-2 `similarity_to_baseline` figures and visual inspection at the review",
            "gate are what settle whether the lower bound is met in substance.",
            "",
        ]
    elif total:
        lines += [
            "The pairs disagree among themselves, which is the most informative outcome of the",
            "three and is reported as-is rather than rounded to a verdict.",
            "",
        ]
    else:
        lines += ["**Not computed** - the required rows are absent.", ""]

    lines += [
        "## Comparison B - this milestone's text-only baseline vs Prototype 1 EXP-002",
        "",
        "The frozen kit means Prototype 1's EXP-002 rows at 512x512, seeds 42/1337/2026,",
        "prompts P1-P4 *should* reproduce as this milestone's baseline. Tested, not promised.",
        "",
        "| prompt | seed | EXP-002 sha256 | EXP-010 sha256 | identical |",
        "|---|---|---|---|---|",
    ]
    previous = {}
    for row in load_rows(("EXP-002",)):
        if row.get("status") != STATUS_OK or int(row.get("width", 0)) != 512 or int(row.get("height", 0)) != 512:
            continue
        previous[(row["prompt_id"], int(row["seed"]))] = row["output_sha256"]

    cross_matches = cross_total = 0
    for key in sorted(baseline):
        if key not in previous:
            continue
        cross_total += 1
        identical = previous[key] == baseline[key]["output_sha256"]
        cross_matches += identical
        lines.append(f"| {key[0]} | {key[1]} | `{previous[key][:16]}...` | "
                     f"`{baseline[key]['output_sha256'][:16]}...` | {'**yes**' if identical else 'no'} |")

    if cross_total == 0:
        lines += ["", "**Not comparable** - no overlapping EXP-002 rows were found.", ""]
    else:
        lines += ["", f"**{cross_matches} of {cross_total} pairs are byte-identical across milestones.**", ""]
        if cross_matches == cross_total:
            lines += [
                "This is a cross-milestone repeatability result: the same pinned model, frozen",
                "prompt kit, scheduler, seed and geometry reproduce the same bytes days apart on",
                "the same machine. It also confirms the M4 baseline is the M3 baseline, so the",
                "two milestones' figures are directly comparable.",
                "",
            ]
        else:
            lines += [
                "Reported as found. A mismatch would indicate that something outside the frozen",
                "kit changed between milestones, and it is recorded rather than explained away.",
                "",
            ]
    return "\n".join(lines)


# --- combined outputs --------------------------------------------------------


def main() -> int:
    rows = load_rows()
    if not rows:
        print("no generation results found", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    write_csv(rows, OUT_DIR / "all-generation-results.csv")

    summary_text = render_summary_markdown(
        summarize(rows), "Prototype 2 cross-method measurements (unscored)"
    )
    summary_text += "\n".join([
        "",
        "## Scope of this table",
        "",
        f"{len(rows)} generation rows across EXP-008 to EXP-013. Measurements only: no quality",
        "judgement, no method selection, no recommendation. Those are the reviewer's, supplied",
        "at the human-review gate.",
        "",
        "Phase-2 similarity indicators are deliberately **absent** from this table. They live in",
        "`docs/evidence/EXP-014/` and were computed in a separate process after all generation",
        "finished, so that no metric model was ever resident in a process whose VRAM and",
        "latency figures appear above.",
        "",
        f"Physical VRAM on this GPU is {PHYSICAL_VRAM_MIB} MiB. Windows WDDM spills into host RAM",
        "without raising a CUDA OOM, so any run exceeding it is flagged rather than caught.",
        "",
    ])
    (OUT_DIR / "measurement-summary.md").write_text(summary_text, encoding="utf-8")

    isolation_text, accepted = process_isolation(rows)
    (OUT_DIR / "process-isolation-check.md").write_text(isolation_text, encoding="utf-8")

    similarity_rows = _load_similarity()
    (OUT_DIR / "monotonicity-check.md").write_text(monotonicity(similarity_rows), encoding="utf-8")
    (OUT_DIR / "lower-bound-diagnostic.md").write_text(lower_bound_diagnostic(rows), encoding="utf-8")
    (OUT_DIR / "copy-risk.md").write_text(copy_risk(similarity_rows), encoding="utf-8")

    ok = sum(1 for r in rows if r["status"] == STATUS_OK)
    print(f"{ok}/{len(rows)} successful generation rows")
    print(f"process isolation: {'ACCEPTED in full' if accepted else 'INCOMPLETE OR REJECTED - see the report'}")
    print(f"similarity rows: {len(similarity_rows)}")
    for name in ("all-generation-results.csv", "measurement-summary.md",
                 "process-isolation-check.md", "monotonicity-check.md",
                 "lower-bound-diagnostic.md", "copy-risk.md"):
        print(f"  {OUT_DIR / name}")
    return 0


def _load_similarity() -> list[dict]:
    import csv as _csv

    rows: list[dict] = []
    directory = EVIDENCE / "EXP-014"
    if not directory.exists():
        return rows
    for path in sorted(directory.glob("similarity-*.csv")):
        with open(path, encoding="utf-8", newline="") as fh:
            rows.extend(list(_csv.DictReader(fh)))
    return rows


if __name__ == "__main__":
    sys.exit(main())
