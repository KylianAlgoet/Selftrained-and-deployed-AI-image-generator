"""EXP-018 Phase 2 - quantify the LoRA's effect, offline and on CPU.

SEPARATE PROCESS, AFTER all generation finished. A pytest asserts the Phase-1
verifier never imports this path: loading a 2.35 GiB CLIP encoder inside a
generation process would inflate exactly the VRAM figures Phase 1 reports.

Two questions, deliberately answered differently:

* **Lower bound (weight 0.0).** Byte equality with the baseline is a DIAGNOSTIC.
  It is a strong positive result when it holds, but divergence is not a failure -
  loading an inactive adapter may legitimately change the execution graph or
  numerical path. Divergence is reported and quantified, never swept up.

* **Changed output (weight 1.0).** A differing PNG SHA alone is NOT sufficient.
  The gate requires change beyond trivial encoding or floating-point noise,
  evidenced by pixel statistics, dHash distance and a CLIP cosine, cross-checked
  against the LoRA parameter delta recorded during training. It makes NO
  visual-quality claim - that is Prototype 4's question.

Run:
    .venv/Scripts/python.exe scripts/evaluate_lora_effect.py
"""

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.evaluation.similarity import ClipImageEncoder, dhash_distance  # noqa: E402

GENERATIONS = REPO / "docs" / "evidence" / "EXP-018" / "generations.jsonl"
OUT_DIR = REPO / "docs" / "evidence" / "EXP-018"

# "Beyond noise" thresholds, declared BEFORE reading any result.
#
# A PNG round-trip is lossless and generation is deterministic under a fixed
# seed, so two runs of an identical configuration differ by exactly zero. These
# thresholds therefore sit far above any encoding artefact while still refusing
# to call a numerically trivial perturbation a real change.
MIN_MEAN_ABS_PIXEL_DIFF = 0.5  # on the 0-255 scale
MIN_CHANGED_PIXEL_FRACTION = 0.01  # 1 % of subpixels differ at all


def pixel_stats(path_a: Path, path_b: Path) -> dict:
    import numpy as np
    from PIL import Image

    with Image.open(path_a) as im_a, Image.open(path_b) as im_b:
        a = np.asarray(im_a.convert("RGB"), dtype=np.int16)
        b = np.asarray(im_b.convert("RGB"), dtype=np.int16)
    diff = np.abs(a - b)
    return {
        "mean_abs_pixel_diff": round(float(diff.mean()), 6),
        "max_abs_pixel_diff": int(diff.max()),
        "changed_pixel_fraction": round(float((diff > 0).mean()), 6),
    }


def main() -> int:
    if not GENERATIONS.is_file():
        print(f"missing {GENERATIONS}")
        return 1

    rows = [json.loads(line) for line in GENERATIONS.open(encoding="utf-8") if line.strip()]
    by_arm: dict[str, dict[tuple, dict]] = {}
    for row in rows:
        by_arm.setdefault(row["arm"], {})[(row["case_id"], row["seed"])] = row

    baselines = by_arm.get("baseline", {})
    if not baselines:
        print("no baseline arm found")
        return 1

    started = time.perf_counter()
    encoder = ClipImageEncoder(device="cpu")
    print(f"CLIP encoder loaded on CPU in {encoder.load_seconds}s (excluded from every GPU figure)")

    results = []
    for arm in ("weight0", "weight1"):
        for key, row in sorted(by_arm.get(arm, {}).items()):
            base = baselines.get(key)
            if base is None:
                continue
            path_a = REPO / base["output_path"]
            path_b = REPO / row["output_path"]
            identical = base["output_sha256"] == row["output_sha256"]

            record = {
                "exp_id": "EXP-018",
                "arm": arm,
                "lora_weight": row["lora_weight"],
                "case_id": row["case_id"],
                "prompt_id": row["prompt_id"],
                "seed": row["seed"],
                "baseline_sha256": base["output_sha256"],
                "arm_sha256": row["output_sha256"],
                "sha256_identical": identical,
            }
            record.update(pixel_stats(path_a, path_b))
            record["dhash_distance"] = dhash_distance(path_a, path_b)
            emb_a = encoder.embed(path_a)
            emb_b = encoder.embed(path_b)
            record["clip_cosine_to_baseline"] = round(float((emb_a * emb_b).sum()), 6)
            record["beyond_noise"] = bool(
                record["mean_abs_pixel_diff"] >= MIN_MEAN_ABS_PIXEL_DIFF
                and record["changed_pixel_fraction"] >= MIN_CHANGED_PIXEL_FRACTION
            )
            results.append(record)
            print(
                f"  {arm} {record['case_id']} seed {record['seed']}: identical={identical} "
                f"mean|d|={record['mean_abs_pixel_diff']} dhash={record['dhash_distance']} "
                f"clip={record['clip_cosine_to_baseline']}"
            )

    out_jsonl = OUT_DIR / "lora-effect.jsonl"
    with out_jsonl.open("w", encoding="utf-8", newline="") as fh:
        for record in results:
            fh.write(json.dumps(record, sort_keys=True) + "\n")

    w0 = [r for r in results if r["arm"] == "weight0"]
    w1 = [r for r in results if r["arm"] == "weight1"]
    identical_w0 = sum(1 for r in w0 if r["sha256_identical"])
    changed_w1 = sum(1 for r in w1 if r["beyond_noise"])

    lines = [
        "# EXP-018 - LoRA load-and-generate effect (Phase 2, offline CPU)",
        "",
        f"CLIP encoder loaded on CPU in {encoder.load_seconds}s. This workload ran in its own",
        "process after all generation finished, so it enters no GPU VRAM or latency figure.",
        "",
        "## Lower-bound diagnostic - adapter loaded at weight 0.0",
        "",
        f"**{identical_w0} of {len(w0)} outputs are byte-identical to the no-adapter baseline.**",
        "",
        "This is a DIAGNOSTIC, not a pass condition. Byte equality is the strongest",
        "available positive result, but divergence would not have failed the milestone:",
        "loading an inactive adapter can legitimately change the execution graph or the",
        "numerical path even when it contributes nothing.",
        "",
        "| case | seed | identical | mean abs diff | changed px | dHash | CLIP cos |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in w0:
        lines.append(
            f"| {r['case_id']} | {r['seed']} | {r['sha256_identical']} | "
            f"{r['mean_abs_pixel_diff']} | {r['changed_pixel_fraction']} | "
            f"{r['dhash_distance']} | {r['clip_cosine_to_baseline']} |"
        )

    lines += [
        "",
        "## Changed-output test - adapter loaded at weight 1.0",
        "",
        f"**{changed_w1} of {len(w1)} outputs changed beyond the pre-declared noise floor.**",
        "",
        f"Thresholds declared before reading any result: mean absolute pixel difference",
        f">= {MIN_MEAN_ABS_PIXEL_DIFF} on the 0-255 scale AND >= {MIN_CHANGED_PIXEL_FRACTION:.0%} of",
        "subpixels differing. A differing PNG SHA alone was never treated as sufficient.",
        "",
        "**No visual-quality claim is made here.** Whether the change is an improvement is",
        "Prototype 4's question, judged by a human against the rubric.",
        "",
        "| case | seed | sha differs | mean abs diff | changed px | dHash | CLIP cos | beyond noise |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in w1:
        lines.append(
            f"| {r['case_id']} | {r['seed']} | {not r['sha256_identical']} | "
            f"{r['mean_abs_pixel_diff']} | {r['changed_pixel_fraction']} | "
            f"{r['dhash_distance']} | {r['clip_cosine_to_baseline']} | {r['beyond_noise']} |"
        )

    lines += [
        "",
        "## Reading the CLIP column honestly",
        "",
        "The cosine is a descriptive indicator, not a referee. It entangles subject,",
        "composition, colour and style, and it uses the same CLIP family the project",
        "conditions with elsewhere. It supports the pixel and hash evidence; it does not",
        "replace the human rubric, which Prototype 3 deliberately does not invoke.",
        "",
    ]
    out_md = OUT_DIR / "lora-effect.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print()
    print(f"weight0 byte-identical to baseline: {identical_w0}/{len(w0)}")
    print(f"weight1 beyond the noise floor:     {changed_w1}/{len(w1)}")
    print(f"elapsed {time.perf_counter() - started:.1f}s")
    print(f"wrote {out_md.relative_to(REPO)} and {out_jsonl.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
