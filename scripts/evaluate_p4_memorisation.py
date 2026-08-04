"""EXP-026 Phase 2 - memorisation and similarity indicators, offline on CPU.

SEPARATE PROCESS, AFTER all generation finished, exactly as M4 established: a
2.35 GiB CLIP encoder resident in a generation process would inflate the very VRAM
figures Phase 1 reports.

Every pilot generation is compared against:
  * its own style's TRAINING images - could the LoRA be reproducing what it saw?
  * the HOLDOUT images - never trained on, so a near match there means something
    about the base model or the prompt rather than about memorisation.

**What these numbers are, stated plainly.** `dhash_distance <= 6` is a coarse
NEAR-COPY INDICATOR. It is not proof of memorisation and it is not a general
memorisation measure: it is sensitive to layout and blind to recolouring, and a
low distance between two flat geometric compositions can happen for reasons that
have nothing to do with training. It FLAGS candidates for human inspection.

**These indicators never decide anything.** They do not populate a rubric cell,
they do not select a checkpoint, and they do not choose a hyperparameter. Flagged
outputs are preserved and surfaced, never deleted - reproducing licensed source
material is a copyright and ethics concern, which is RQ11 in
`docs/01-research-plan.md`.

Run:
    .venv/Scripts/python.exe scripts/evaluate_p4_memorisation.py
"""

import csv
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.evaluation.similarity import COPY_RISK_MAX_DHASH_DISTANCE, ClipImageEncoder  # noqa: E402
from ml.training import style_kit  # noqa: E402

GENERATIONS = REPO / "docs" / "evidence" / "EXP-025" / "pilot-matrix.jsonl"
OUT_DIR = REPO / "docs" / "evidence" / "EXP-026"
MANIFEST_DIR = REPO / "data" / "manifests"
DATASET_MANIFEST = MANIFEST_DIR / "dataset-v1.csv"


def dhash_of(path: Path):
    from ml.dataset.hashing import dhash_file

    return dhash_file(path)


def main() -> int:
    if not GENERATIONS.is_file():
        print(f"missing {GENERATIONS}")
        return 1

    rows = [json.loads(line) for line in GENERATIONS.open(encoding="utf-8") if line.strip()]
    print(f"{len(rows)} pilot generations to evaluate")

    # Reference sets, per style: the training images the LoRA saw, and the
    # holdout images it never saw.
    dataset = list(csv.DictReader(DATASET_MANIFEST.open(encoding="utf-8")))
    train_refs: dict[str, list[tuple[str, Path]]] = {}
    holdout_refs: list[tuple[str, Path]] = []
    for style in style_kit.STYLE_ORDER:
        manifest = list(
            csv.DictReader((MANIFEST_DIR / f"style-{style}-p4.csv").open(encoding="utf-8"))
        )
        train_refs[style] = [(r["id"], REPO / r["source_path"]) for r in manifest]
    for r in dataset:
        if r["split"] == "holdout":
            holdout_refs.append((r["id"], REPO / "data" / "raw" / r["style"] / r["filename"]))
    print(f"reference sets: " + ", ".join(f"{s} {len(train_refs[s])}" for s in train_refs))
    print(f"holdout: {len(holdout_refs)} images (never trained on)")

    started = time.perf_counter()

    # dHash pass - cheap, so every reference is hashed once and reused.
    train_hashes = {s: [(i, dhash_of(p)) for i, p in refs] for s, refs in train_refs.items()}
    holdout_hashes = [(i, dhash_of(p)) for i, p in holdout_refs]
    print(f"reference hashes computed in {time.perf_counter() - started:.1f}s")

    encoder = ClipImageEncoder(device="cpu")
    print(f"CLIP encoder loaded on CPU in {encoder.load_seconds}s (excluded from every GPU figure)")

    results = []
    flagged = 0
    for n, row in enumerate(rows, start=1):
        out_path = REPO / row["output_path"]
        if not out_path.is_file():
            continue
        style = row["style"]
        gen_hash = dhash_of(out_path)

        train_d = [(i, int(gen_hash - h)) for i, h in train_hashes[style]]
        nearest_train_id, nearest_train_d = min(train_d, key=lambda kv: kv[1])
        hold_d = [(i, int(gen_hash - h)) for i, h in holdout_hashes]
        nearest_hold_id, nearest_hold_d = min(hold_d, key=lambda kv: kv[1])

        gen_emb = encoder.embed(out_path)
        best_id, best_cos = "", -1.0
        for ref_id, ref_path in train_refs[style]:
            cos = float((gen_emb * encoder.embed(ref_path)).sum())
            if cos > best_cos:
                best_id, best_cos = ref_id, cos

        is_flagged = nearest_train_d <= COPY_RISK_MAX_DHASH_DISTANCE
        flagged += int(is_flagged)
        results.append(
            {
                "exp_id": "EXP-026",
                "arm": row["arm"],
                "style": style,
                "checkpoint_step": row["checkpoint_step"],
                "prompt_id": row["prompt_id"],
                "seed": row["seed"],
                "lora_weight": row["lora_weight"],
                "output_path": row["output_path"],
                "output_sha256": row["output_sha256"],
                "nearest_training_item": nearest_train_id,
                "nearest_training_dhash": nearest_train_d,
                "nearest_holdout_item": nearest_hold_id,
                "nearest_holdout_dhash": nearest_hold_d,
                "max_clip_cosine_to_training": round(best_cos, 6),
                "most_similar_training_item_clip": best_id,
                "near_copy_flag": is_flagged,
            }
        )
        if n % 25 == 0:
            print(f"  {n}/{len(rows)} evaluated")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "memorisation-indicators.jsonl").open("w", encoding="utf-8", newline="") as fh:
        for record in results:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
    if results:
        with (OUT_DIR / "memorisation-indicators.csv").open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(results[0]))
            writer.writeheader()
            writer.writerows(results)

    # Per-arm summary
    by_arm: dict[str, list[dict]] = {}
    for record in results:
        by_arm.setdefault(record["arm"], []).append(record)

    lines = [
        "# EXP-026 — memorisation and similarity indicators (Phase 2, offline CPU)",
        "",
        f"{len(results)} pilot generations, compared against each style's **training** images and",
        f"against the **holdout** images that were never trained on. CLIP encoder loaded on CPU in",
        f"{encoder.load_seconds}s, in its own process after all generation finished, so it enters no",
        "GPU VRAM or latency figure.",
        "",
        "## What these numbers are — and are not",
        "",
        f"`dhash <= {COPY_RISK_MAX_DHASH_DISTANCE}` is a **coarse near-copy INDICATOR**, kept at the",
        "M4 threshold for continuity. **It is not proof of memorisation** and not a general",
        "memorisation measure: it is sensitive to layout, blind to recolouring, and two flat",
        "geometric compositions can score close for reasons unrelated to training.",
        "",
        "**These indicators decide nothing.** They populate no rubric cell, select no checkpoint,",
        "and choose no hyperparameter. Any flagged output is preserved and surfaced for human",
        "inspection, never deleted.",
        "",
        "## Per-arm summary",
        "",
        "| arm | style | n | median dHash to train | min dHash to train | flagged | median dHash to holdout | median CLIP cos to train |",
        "|---|---|---|---|---|---|---|---|",
    ]
    import statistics

    for arm in sorted(by_arm):
        recs = by_arm[arm]
        td = [r["nearest_training_dhash"] for r in recs]
        hd = [r["nearest_holdout_dhash"] for r in recs]
        cc = [r["max_clip_cosine_to_training"] for r in recs]
        lines.append(
            f"| `{arm}` | {recs[0]['style']} | {len(recs)} | {statistics.median(td):.1f} | "
            f"{min(td)} | **{sum(1 for r in recs if r['near_copy_flag'])}** | "
            f"{statistics.median(hd):.1f} | {statistics.median(cc):.4f} |"
        )

    lines += [
        "",
        f"**{flagged} of {len(results)} generations carry a near-copy flag.**",
        "",
        "The holdout column is the control: those images were never trained on, so a distance",
        "there similar to the training distance suggests the similarity comes from the base model",
        "or the prompt rather than from memorisation.",
        "",
    ]
    if flagged:
        lines += ["## Flagged outputs — preserved, for human inspection", "",
                  "| arm | prompt | seed | weight | nearest training item | dHash | output |",
                  "|---|---|---|---|---|---|---|"]
        for r in results:
            if r["near_copy_flag"]:
                lines.append(
                    f"| `{r['arm']}` | {r['prompt_id']} | {r['seed']} | {r['lora_weight']} | "
                    f"{r['nearest_training_item']} | **{r['nearest_training_dhash']}** | "
                    f"`{r['output_path']}` |"
                )
        lines.append("")

    (OUT_DIR / "memorisation-indicators.md").write_text("\n".join(lines), encoding="utf-8")

    print()
    print(f"near-copy flagged: {flagged}/{len(results)}")
    print(f"elapsed {time.perf_counter() - started:.1f}s")
    print(f"wrote {(OUT_DIR / 'memorisation-indicators.md').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
