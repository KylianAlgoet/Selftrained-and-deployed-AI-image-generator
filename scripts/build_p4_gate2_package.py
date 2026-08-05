"""Build the Gate-2 review package: labelled contact sheets and a BLANK form.

Unlike Gate 1, these sheets are **labelled**. Gate 1 blinded the arms because it
compared arms that differed in one hidden variable each. Gate 2 asks a different
question - which checkpoint goes to production - and that question cannot be
answered without knowing which checkpoint is which.

One sheet per (arm, checkpoint, geometry), matching one OS process in EXP-031, so
a sheet always corresponds to exactly one measured generation arm.

**The form ships blank.** No score is pre-filled, no candidate is marked preferred,
and no visual-quality claim appears anywhere in this package or in Phase B.

Run:
    .venv/Scripts/python.exe scripts/build_p4_gate2_package.py
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.dataset.contact_sheet import make_contact_sheet  # noqa: E402
from ml.training import final_matrix as fm  # noqa: E402

GENERATIONS = REPO / "docs" / "evidence" / "EXP-031" / "final-matrix.jsonl"
SHEETS = REPO / "docs" / "evidence" / "prototype-4" / "final-sheets"
FORM = REPO / "docs" / "evidence" / "prototype-4" / "gate-2-scoring-form.md"

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


def sheet_label(row: dict) -> str:
    geometry = f"{row['width']}x{row['height']}"
    if row["arm"] == "BASE":
        return f"BASE__{row['style']}__{geometry}"
    return f"{row['arm']}__{row['style']}__ck{row['checkpoint_step']:05d}__{geometry}"


def main() -> int:
    if not GENERATIONS.is_file():
        print(f"missing {GENERATIONS}")
        return 1
    rows = [json.loads(line) for line in GENERATIONS.open(encoding="utf-8") if line.strip()]
    print(f"{len(rows)} generations")

    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(sheet_label(row), []).append(row)

    SHEETS.mkdir(parents=True, exist_ok=True)

    def cell_sort(r: dict):
        return (r["prompt_id"], r["seed"], r["lora_weight"] if r["lora_weight"] is not None else -1.0)

    index = []
    for label in sorted(groups):
        ordered = sorted(groups[label], key=cell_sort)
        paths = [REPO / r["output_path"] for r in ordered]
        missing = [p for p in paths if not p.is_file()]
        if missing:
            print(f"  {label}: {len(missing)} missing images, skipped")
            continue
        out = SHEETS / f"{label}.jpg"
        make_contact_sheet(paths, out, columns=4)
        index.append((label, ordered[0]["style"], len(ordered), out, ordered))
        print(f"  {label:52s} {len(ordered):3d} images -> {out.stat().st_size // 1024:4d} KB")

    # --- the blank form -------------------------------------------------------
    lines = [
        "# Prototype 4 — Gate 2 scoring form (BLANK)",
        "",
        "**Gate 2.** Score the sheets in `final-sheets/`, then return the decisions in the last",
        "section. Nothing in Phase B selected a production checkpoint, declared a winner, or made",
        "any visual-quality claim — those are yours.",
        "",
        "## Why these sheets are labelled",
        "",
        "Gate 1 was blinded because it compared arms differing in one hidden variable each —",
        "style-only versus verbatim, 12 versus 24 versus 44, 150 versus 300. Gate 2 asks which",
        "checkpoint goes to production, and that question cannot be answered without knowing which",
        "checkpoint each sheet is. **The trade-off is stated rather than hidden:** labelled sheets",
        "carry an expectation effect that blinded ones do not.",
        "",
        "`BASE__*` sheets are the untrained SD 1.5 control on identical prompt text.",
        "",
        "## Prompt roles",
        "",
        "| id | role | what it probes |",
        "|---|---|---|",
    ]
    for p in fm.FINAL_PROMPTS:
        lines.append(f"| `{p.id}` | {p.role} | {p.intent} |")

    lines += [
        "",
        "`FP4-style-free` carries **no trigger and no style phrase**. A style LoRA should leave it",
        "close to the base model; drift there is leakage, not style learning.",
        "",
        "## Sheets to score",
        "",
        "| sheet | style | images | cells |",
        "|---|---|---:|---|",
    ]
    for label, style, n, path, ordered in index:
        prompts = sorted({r["prompt_id"] for r in ordered})
        weights = sorted({r["lora_weight"] for r in ordered if r["lora_weight"] is not None})
        wtxt = ", ".join(f"{w:g}" for w in weights) if weights else "base"
        lines.append(f"| `{label}` | {style} | {n} | prompts {', '.join(prompts)}; weights {wtxt} |")

    lines += [
        "",
        "Every sheet is ordered deterministically by **(prompt, seed, LoRA weight)**, 4 columns.",
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
        "back-filled — the M3/M4/M5 rule. `reference_influence` is absent from the LoRA-alone",
        "sheets because they use no reference image.",
        "",
        "## Scores",
        "",
        "| sheet | " + " | ".join(f"`{n}`" for n, _, _ in RUBRIC) + " |",
        "|---" * (len(RUBRIC) + 1) + "|",
    ]
    for label, _, _, _, _ in index:
        lines.append(f"| `{label}` | " + " | ".join("" for _ in RUBRIC) + " |")

    lines += [
        "",
        "## Failure-mode probe",
        "",
        "Mark `worse`, `same`, `better` or leave blank, against the `BASE__*` sheet for that style",
        "and geometry.",
        "",
        "| sheet | " + " | ".join(f"`{m}`" for m in FAILURE_MODES) + " |",
        "|---" * (len(FAILURE_MODES) + 1) + "|",
    ]
    for label, _, _, _, _ in index:
        if not label.startswith("BASE__"):
            lines.append(f"| `{label}` | " + " | ".join("" for _ in FAILURE_MODES) + " |")

    lines += [
        "",
        "## Decisions Gate 2 needs from you",
        "",
        "None of these has been made for you, and none may be inferred from an automated indicator.",
        "",
        "1. **Final production checkpoint per style** — which arm and step for minimal-geometric,",
        "   ukiyo-e and retro-poster, or *none* for a style that did not reach a usable state.",
        "2. **Default LoRA weight** for the application, from the 0.0 / 0.4 / 0.7 / 1.0 sweep.",
        "3. **RQ5 verdict** — does the balanced multi-style LoRA match the per-style LoRAs, or do",
        "   separate per-style adapters stay? Include whether you see cross-style token bleed.",
        "4. **H4 verdict** — does `retro-poster` bake in frames or pseudo-text? This was left",
        "   unanswered at Gate 1 on purpose.",
        "5. **H5 verdict** — do style strength and prompt adherence trade off as weight rises?",
        "6. **Per-style outcome** — pass / partial pass / failure for each style, per the criteria",
        "   in the approved plan. A partial pass is never upgraded, and a failed style is recorded",
        "   as failed rather than dropped.",
        "7. **Contingency** — whether any contingency run is now authorised and which SINGLE",
        "   variable it may change. Both slots are still unused.",
        "8. **DR-010** — whether the draft may be finalised with your conclusion.",
        "",
        "## Not decided, and not decidable from this package",
        "",
        "- No production checkpoint has been selected and no style is described as better.",
        "- **No visual-quality claim is made anywhere in Phase B.**",
        "- The indicators in `docs/evidence/EXP-033/` are descriptive only. They populate no cell",
        "  above and may not select a checkpoint, style or hyperparameter.",
        "- `DR-010` is a **draft with no conclusion** until you complete this gate.",
        "",
    ]
    FORM.write_text("\n".join(lines), encoding="utf-8")
    total_kb = sum(p.stat().st_size for _, _, _, p, _ in index) / 1024
    print(f"\nform   -> {FORM.relative_to(REPO)}")
    print(f"{len(index)} sheets, {total_kb:.0f} KB total")
    oversize = [(lab, p.stat().st_size // 1024) for lab, _, _, p, _ in index if p.stat().st_size > 300 * 1024]
    if oversize:
        print("WARNING sheets above the 300 KB convention:")
        for lab, kb in oversize:
            print(f"  {lab} {kb} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
