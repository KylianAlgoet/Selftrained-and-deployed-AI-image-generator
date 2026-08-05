"""EXP-033 Phase 2 - final-matrix similarity, diversity and near-copy indicators.

Offline, CPU only, in its own process AFTER all EXP-031 generation finished. A
2.35 GiB CLIP encoder resident in a generation process would inflate the very VRAM
figures Phase 1 reports, which is why M4 established this boundary and why a
pytest enforces it in both directions.

Three descriptive indicators:

  * **near-copy** - dHash to each style's TRAINING images, and to the HOLDOUT
    images the model never saw, which is the control;
  * **similarity** - max CLIP cosine to the training set;
  * **diversity** - mean pairwise CLIP distance across SEEDS within an otherwise
    identical cell, so a mode-collapsed checkpoint is visible as a number.

**What these numbers are, stated plainly.** `dhash_distance <= 6` is a coarse
NEAR-COPY INDICATOR. It is not proof of memorisation and it is not a general
memorisation measure: it is sensitive to layout and blind to recolouring.

**These indicators decide nothing.** They populate no rubric cell, they select no
checkpoint, style or hyperparameter, and they may not be read as a quality
ranking. Flagged outputs are preserved and surfaced, never deleted - reproducing
licensed source material is RQ11 in `docs/01-research-plan.md`.

Run:
    .venv/Scripts/python.exe scripts/evaluate_p4_final_indicators.py
"""

import csv
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.evaluation.similarity import COPY_RISK_MAX_DHASH_DISTANCE, ClipImageEncoder  # noqa: E402
from ml.training import style_kit  # noqa: E402

GENERATIONS = REPO / "docs" / "evidence" / "EXP-031" / "final-matrix.jsonl"
OUT_DIR = REPO / "docs" / "evidence" / "EXP-033"
MANIFEST_DIR = REPO / "data" / "manifests"
DATASET_MANIFEST = MANIFEST_DIR / "dataset-v1.csv"


def dhash_of(path: Path):
    from ml.dataset.hashing import dhash_file

    return dhash_file(path)


def cell_key(row: dict) -> tuple:
    """Everything identical except the seed - the unit diversity is measured over."""
    return (
        row["arm"],
        row["checkpoint_step"],
        row["style"],
        row["prompt_id"],
        row["lora_weight"],
        f"{row['width']}x{row['height']}",
    )


def group_key(row: dict) -> str:
    return f"{row['arm']}@{row['checkpoint_step']}/{row['width']}x{row['height']}"


def main() -> int:
    if not GENERATIONS.is_file():
        print(f"missing {GENERATIONS}")
        return 1

    rows = [json.loads(line) for line in GENERATIONS.open(encoding="utf-8") if line.strip()]
    print(f"{len(rows)} final-matrix generations to evaluate")

    dataset = list(csv.DictReader(DATASET_MANIFEST.open(encoding="utf-8")))
    train_refs: dict[str, list[tuple[str, Path]]] = {}
    for style in style_kit.STYLE_ORDER:
        manifest = list(
            csv.DictReader((MANIFEST_DIR / f"style-{style}-p4.csv").open(encoding="utf-8"))
        )
        train_refs[style] = [(r["id"], REPO / r["source_path"]) for r in manifest]
    holdout_refs = [
        (r["id"], REPO / "data" / "raw" / r["style"] / r["filename"])
        for r in dataset
        if r["split"] == "holdout"
    ]
    print("reference sets: " + ", ".join(f"{s} {len(train_refs[s])}" for s in train_refs))
    print(f"holdout: {len(holdout_refs)} images (never trained on)")

    started = time.perf_counter()
    train_hashes = {s: [(i, dhash_of(p)) for i, p in refs] for s, refs in train_refs.items()}
    holdout_hashes = [(i, dhash_of(p)) for i, p in holdout_refs]
    print(f"reference hashes computed in {time.perf_counter() - started:.1f}s")

    encoder = ClipImageEncoder(device="cpu")
    print(f"CLIP encoder loaded on CPU in {encoder.load_seconds}s (excluded from every GPU figure)")

    ref_embeddings = {
        style: [(i, encoder.embed(p)) for i, p in refs] for style, refs in train_refs.items()
    }
    print(f"reference embeddings computed in {time.perf_counter() - started:.1f}s")

    results = []
    embeddings: dict[str, object] = {}
    flagged = 0
    for n, row in enumerate(rows, start=1):
        out_path = REPO / row["output_path"]
        if not out_path.is_file():
            continue
        style = row["style"]
        gen_hash = dhash_of(out_path)

        nearest_train_id, nearest_train_d = min(
            ((i, int(gen_hash - h)) for i, h in train_hashes[style]), key=lambda kv: kv[1]
        )
        nearest_hold_id, nearest_hold_d = min(
            ((i, int(gen_hash - h)) for i, h in holdout_hashes), key=lambda kv: kv[1]
        )

        gen_emb = encoder.embed(out_path)
        embeddings[row["output_path"]] = gen_emb
        best_id, best_cos = "", -1.0
        for ref_id, ref_emb in ref_embeddings[style]:
            cos = float((gen_emb * ref_emb).sum())
            if cos > best_cos:
                best_id, best_cos = ref_id, cos

        is_flagged = nearest_train_d <= COPY_RISK_MAX_DHASH_DISTANCE
        flagged += int(is_flagged)
        results.append(
            {
                "exp_id": "EXP-033",
                "arm": row["arm"],
                "kind": row.get("kind", ""),
                "style": style,
                "checkpoint_step": row["checkpoint_step"],
                "prompt_id": row["prompt_id"],
                "prompt_role": row["prompt_role"],
                "seed": row["seed"],
                "lora_weight": row["lora_weight"],
                "geometry": f"{row['width']}x{row['height']}",
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
        if n % 50 == 0:
            print(f"  {n}/{len(rows)} evaluated")

    # --- diversity across seeds ------------------------------------------------
    # One entry per DISTINCT seed. The executed matrix repeated 24 configurations
    # (blocks A and B overlap at weight 0.7), and those repeats are byte-identical,
    # so counting them would pair an image with itself and drag every affected
    # cell's mean pairwise distance toward zero - manufacturing "mode collapse"
    # out of an orchestration bug.
    cells: dict[tuple, dict[int, dict]] = {}
    duplicates_skipped = 0
    for row in rows:
        if row["output_path"] not in embeddings:
            continue
        bucket = cells.setdefault(cell_key(row), {})
        if row["seed"] in bucket:
            duplicates_skipped += 1
            continue
        bucket[row["seed"]] = row
    if duplicates_skipped:
        print(f"diversity: skipped {duplicates_skipped} repeated configurations")

    diversity = []
    for key, bucket in sorted(cells.items(), key=lambda kv: str(kv[0])):
        members = [bucket[s] for s in sorted(bucket)]
        if len(members) < 2:
            continue
        distances = []
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a = embeddings[members[i]["output_path"]]
                b = embeddings[members[j]["output_path"]]
                distances.append(1.0 - float((a * b).sum()))
        diversity.append(
            {
                "exp_id": "EXP-033",
                "arm": key[0],
                "checkpoint_step": key[1],
                "style": key[2],
                "prompt_id": key[3],
                "lora_weight": key[4],
                "geometry": key[5],
                "seeds": len(members),
                "mean_pairwise_clip_distance": round(statistics.fmean(distances), 6),
                "min_pairwise_clip_distance": round(min(distances), 6),
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "final-indicators.jsonl").open("w", encoding="utf-8", newline="") as fh:
        for record in results:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
    if results:
        with (OUT_DIR / "final-indicators.csv").open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(results[0]))
            writer.writeheader()
            writer.writerows(results)
    with (OUT_DIR / "diversity-indicators.csv").open("w", encoding="utf-8", newline="") as fh:
        if diversity:
            writer = csv.DictWriter(fh, fieldnames=list(diversity[0]))
            writer.writeheader()
            writer.writerows(diversity)

    by_group: dict[str, list[dict]] = {}
    for record, row in zip(results, [r for r in rows if r["output_path"] in embeddings]):
        by_group.setdefault(group_key(row), []).append(record)

    lines = [
        "# EXP-033 — final-matrix indicators (Phase 2, offline CPU)",
        "",
        f"{len(results)} generations from the EXP-031 final validation matrix, compared against",
        "each style's **training** images and against the **holdout** images that were never",
        f"trained on. CLIP encoder loaded on CPU in {encoder.load_seconds}s, in its own process",
        "after all generation finished, so it enters no GPU VRAM or latency figure.",
        "",
        "## What these numbers are — and are not",
        "",
        f"`dhash <= {COPY_RISK_MAX_DHASH_DISTANCE}` is a **coarse near-copy INDICATOR**, kept at the",
        "M4 threshold for continuity. **It is not proof of memorisation** and not a general",
        "memorisation measure: it is sensitive to layout, blind to recolouring, and two flat",
        "geometric compositions can score close for reasons unrelated to training.",
        "",
        "**These indicators decide nothing.** They populate no rubric cell, select no checkpoint,",
        "style or hyperparameter, and are not a quality ranking. Any flagged output is preserved",
        "and surfaced for human inspection, never deleted.",
        "",
        "## Per-arm summary",
        "",
        "| arm@step/geometry | style | n | median dHash to train | min | flagged | median dHash to holdout | median CLIP cos |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for group in sorted(by_group):
        recs = by_group[group]
        td = [r["nearest_training_dhash"] for r in recs]
        hd = [r["nearest_holdout_dhash"] for r in recs]
        cc = [r["max_clip_cosine_to_training"] for r in recs]
        styles = sorted({r["style"] for r in recs})
        lines.append(
            f"| `{group}` | {','.join(styles)} | {len(recs)} | {statistics.median(td):.1f} | "
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
        "## Diversity across seeds",
        "",
        "Mean pairwise CLIP distance between generations that differ **only** in seed. A low",
        "number means the cell produces near-identical images regardless of seed. It is",
        "descriptive: what counts as too low is a human judgement at Gate 2.",
        "",
        "| arm@step | style | prompt | weight | geometry | seeds | mean pairwise distance | min |",
        "|---|---|---|---:|---|---:|---:|---:|",
    ]
    for d in sorted(
        diversity, key=lambda d: (d["arm"], d["checkpoint_step"], d["style"], d["prompt_id"])
    ):
        lines.append(
            f"| `{d['arm']}@{d['checkpoint_step']}` | {d['style']} | {d['prompt_id']} | "
            f"{d['lora_weight']} | {d['geometry']} | {d['seeds']} | "
            f"{d['mean_pairwise_clip_distance']:.4f} | {d['min_pairwise_clip_distance']:.4f} |"
        )

    if flagged:
        lines += ["", "## Flagged outputs — preserved, for human inspection", "",
                  "| arm | step | prompt | seed | weight | geometry | nearest training item | dHash | output |",
                  "|---|---:|---|---:|---:|---|---|---:|---|"]
        for r in results:
            if r["near_copy_flag"]:
                lines.append(
                    f"| `{r['arm']}` | {r['checkpoint_step']} | {r['prompt_id']} | {r['seed']} | "
                    f"{r['lora_weight']} | {r['geometry']} | {r['nearest_training_item']} | "
                    f"**{r['nearest_training_dhash']}** | `{r['output_path']}` |"
                )
    lines.append("")

    (OUT_DIR / "final-indicators.md").write_text("\n".join(lines), encoding="utf-8")

    print()
    print(f"near-copy flagged: {flagged}/{len(results)}")
    print(f"diversity cells:   {len(diversity)}")
    print(f"elapsed {time.perf_counter() - started:.1f}s")
    print(f"wrote {(OUT_DIR / 'final-indicators.md').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
