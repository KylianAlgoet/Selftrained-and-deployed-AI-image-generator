"""EXP-014 - Phase-2 offline similarity evaluation.

Runs AFTER all generation is finished, in its OWN process, over the images on
disk, on CPU by default. It generates nothing and measures no generation method.

This separation is the structural correction of the M4 plan. The CLIP image
encoder loaded here is 2.35 GiB; loading it inside a text-only or img2img
generation process purely to compute an indicator would have inflated exactly the
VRAM figures the RQ6 method comparison rests on - the same class of error as the
EXP-005 allocator contamination, one milestone later.

Its output goes to a SEPARATE file joined on `output_sha256`. No similarity value
is ever written into a generation row, and the evaluation device plus the pinned
encoder revision travel with every indicator so this workload can never be
mistaken for part of a generation figure.

EXP-007 is excluded on purpose: it is an environment gate, not a comparison arm,
and its text-only run would otherwise compete with EXP-010's for the same
baseline cell.

Run:
    .venv/Scripts/python.exe scripts/evaluate_similarity.py
    .venv/Scripts/python.exe scripts/evaluate_similarity.py --device cuda
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.evaluation.similarity import evaluate  # noqa: E402
from ml.inference.reference_schema import (  # noqa: E402
    read_jsonl,
    write_similarity_csv,
)

EVIDENCE = REPO / "docs" / "evidence"

# The comparison arms. EXP-007 is deliberately absent (see the module docstring).
SOURCE_EXPERIMENTS = ("EXP-008", "EXP-008b", "EXP-009", "EXP-009b", "EXP-010",
                      "EXP-011", "EXP-012", "EXP-013")


def collect_generation_rows(experiments: tuple[str, ...]) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    sources: list[str] = []
    for exp_id in experiments:
        directory = EVIDENCE / exp_id
        if not directory.exists():
            continue
        for path in sorted(directory.glob("results-*.jsonl")):
            found = read_jsonl(path)
            rows.extend(found)
            sources.append(f"{path.relative_to(REPO)} ({len(found)} rows)".replace("\\", "/"))
    return rows, sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--device", default="cpu", choices=["cpu", "cuda"],
        help="CPU by default. A CUDA pass is recorded as its own labelled evaluation "
             "workload and is still excluded from every generation figure.",
    )
    parser.add_argument("--exp", default="EXP-014")
    args = parser.parse_args(argv)

    generation_rows, sources = collect_generation_rows(SOURCE_EXPERIMENTS)
    if not generation_rows:
        print("no generation rows found - run the Phase-1 experiments first", file=sys.stderr)
        return 1

    print(f"generation rows read: {len(generation_rows)}")
    for source in sources:
        print(f"  {source}")
    print(f"evaluating on {args.device} with the pinned CLIP image encoder ...")

    def progress(done: int, total: int) -> None:
        print(f"  {done}/{total}", flush=True)

    rows, run_record = evaluate(
        generation_rows, REPO, exp_id=args.exp, device=args.device, progress=progress
    )

    out_dir = EVIDENCE / args.exp
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = write_similarity_csv(rows, out_dir / f"similarity-{args.device}.csv")
    run_record["sources"] = sources
    record_path = out_dir / f"evaluation-run-{args.device}.json"
    record_path.write_text(json.dumps(run_record, indent=2) + "\n", encoding="utf-8")

    failed = [r for r in rows if r.status != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} images evaluated in {run_record['evaluation_seconds']}s")
    print(f"encoder load: {run_record['encoder_load_seconds']}s on {args.device}")
    print(f"copy-risk flagged (dhash <= {run_record['copy_risk_threshold_dhash']}): {run_record['copy_risk_flagged']}")
    for row in failed[:10]:
        print(f"  FAILED {row.output_sha256[:12]}: {row.error_type}: {row.error_message[:120]}")
    print(f"\nindicators: {csv_path}")
    print(f"run record: {record_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
