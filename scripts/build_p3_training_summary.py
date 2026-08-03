"""Render the Prototype 3 training results into committed evidence.

Reads only the JSONL rows the runners actually wrote; it computes nothing that a
run did not measure and never fills a gap with an estimate.

Run:
    .venv/Scripts/python.exe scripts/build_p3_training_summary.py
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.training.lora_schema import read_jsonl, render_summary_markdown, write_csv  # noqa: E402

# Physical VRAM of the audited device, from EXP-001. Stated on every table so a
# peak is never reported without the ceiling it sits under (risk R12).
DEVICE_TOTAL_MB = 8187.5

SOURCES = [
    ("EXP-016", REPO / "docs" / "evidence" / "EXP-016" / "training-runs.jsonl"),
    ("EXP-017", REPO / "docs" / "evidence" / "EXP-017" / "training-runs.jsonl"),
]


def main() -> int:
    all_rows: list[dict] = []
    for exp_id, path in SOURCES:
        if not path.is_file():
            print(f"skipping {exp_id}: {path} does not exist")
            continue
        rows = read_jsonl(path)
        print(f"{exp_id}: {len(rows)} rows")
        write_csv(rows, path.with_suffix(".csv"))
        all_rows.extend(rows)

    if not all_rows:
        print("no rows found; nothing written")
        return 1

    out = REPO / "docs" / "evidence" / "prototype-3" / "training-summary.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    markdown = render_summary_markdown(
        all_rows,
        "Prototype 3 - LoRA training measurements",
        device_total_mb=DEVICE_TOTAL_MB,
    )

    lines = [markdown, "", "## Phase-separated peaks", ""]
    lines.append("| exp | geometry | post-load alloc | fwd+bwd peak | optimizer peak | RSS |")
    lines.append("|---|---|---|---|---|---|")
    for row in all_rows:
        res = row["resources"]
        lines.append(
            f"| {row['exp_id']} | {row['width']}x{row['height']} | "
            f"{res['post_load_allocated_mb']} | {res['peak_forward_backward_allocated_mb']} | "
            f"{res['peak_optimizer_step_allocated_mb']} | {res['peak_process_rss_mb']} |"
        )

    lines += ["", "## Technical gates", ""]
    lines.append("| exp | trainable tensors | parameters | base frozen | grads finite/non-zero | L2 delta | first loss | last loss |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for row in all_rows:
        g = row["gates"]
        lines.append(
            f"| {row['exp_id']} | {g['trainable_lora_tensors']} | {g['trainable_lora_parameters']} | "
            f"{g['base_unet_parameters_frozen']} | "
            f"{g['gradients_finite']}/{g['gradients_nonzero']} | {g['lora_params_l2_delta']} | "
            f"{g['first_loss']:.6f} | {g['last_loss']:.6f} |"
        )

    lines += [
        "",
        "`loss_decreased` is recorded per run but is deliberately NOT a pass condition: a run",
        "this short on 12 images is far too noisy for the trend to carry weight.",
        "",
        "## Saved adapters (outside git)",
        "",
        "| exp | bytes | tensors | LoRA keys | unexpected base-model keys | sha256 |",
        "|---|---|---|---|---|---|",
    ]
    for row in all_rows:
        a = row["adapter"]
        unexpected = a["unexpected_base_model_keys"] or "none"
        lines.append(
            f"| {row['exp_id']} | {a['size_bytes']} | {a['tensor_count']} | {a['lora_key_count']} | "
            f"{unexpected} | `{a['sha256'][:16]}...` |"
        )

    lines += ["", "## Reset boundaries", ""]
    for row in all_rows:
        lines.append(f"- **{row['exp_id']}**: {row['resources']['reset_boundaries']}")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
