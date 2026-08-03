"""Orchestrate the Prototype 3 (M5) LoRA training probes as isolated processes.

Two jobs, both of which exist because of earlier measured mistakes:

1. **Process isolation.** Every phase runs in a FRESH subprocess. The caching
   allocator retains its pool across `reset_peak_memory_stats()`, which corrupted
   EXP-005's first run and inflated one strategy by ~2x for provably identical
   work. One configuration per OS process is not a style preference here.

2. **Micro-gating.** Nothing long starts before something short has proved the
   loop works, and the plan's run limits are enforced rather than hoped for:
     * no preliminary probe may exceed 20 minutes;
     * the 512x512 smoke run does not start until the 1-step and 5-10-step
       probes have passed AND a projected wall-clock has been reported;
     * a projection above 60 minutes STOPS and asks, rather than proceeding.

The 512x1536 arm is a FEASIBILITY probe only. It deliberately offers no smoke
phase: establishing native training cost is M5's question, native style quality
is M6's, and that expansion needs a separate decision.

Run:
    .venv/Scripts/python.exe scripts/run_lora_training.py --plan
    .venv/Scripts/python.exe scripts/run_lora_training.py --stage 512-probe
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.training.lora_schema import (  # noqa: E402
    PHASE_SINGLE_STEP,
    PHASE_SMOKE,
    PHASE_STABILITY,
    SMOKE_WALL_ASK_THRESHOLD_SECONDS,
    read_jsonl,
)

PYTHON = REPO / ".venv" / "Scripts" / "python.exe"

# The stability probe's step count. 10 is the top of the plan's 5-10 band: enough
# to see whether the loss is finite and the step time is stable, still far below
# the 20-minute probe ceiling.
STABILITY_STEPS = 10

# The 512x512 smoke run length. Chosen to be long enough to move the weights
# measurably on 12 images, short enough to stay well inside the run limits.
SMOKE_STEPS = 300

STAGES: dict[str, list[dict]] = {
    "512-probe": [
        {
            "exp_id": "EXP-016a",
            "phase": PHASE_SINGLE_STEP,
            "width": 512,
            "height": 512,
            "steps": 1,
            "results": "docs/evidence/EXP-016/training-runs.jsonl",
        },
        {
            "exp_id": "EXP-016b",
            "phase": PHASE_STABILITY,
            "width": 512,
            "height": 512,
            "steps": STABILITY_STEPS,
            "results": "docs/evidence/EXP-016/training-runs.jsonl",
        },
    ],
    "512-smoke": [
        {
            "exp_id": "EXP-016",
            "phase": PHASE_SMOKE,
            "width": 512,
            "height": 512,
            "steps": SMOKE_STEPS,
            "results": "docs/evidence/EXP-016/training-runs.jsonl",
        },
    ],
    "1536-probe": [
        {
            "exp_id": "EXP-017a",
            "phase": PHASE_SINGLE_STEP,
            "width": 512,
            "height": 1536,
            "steps": 1,
            "results": "docs/evidence/EXP-017/training-runs.jsonl",
        },
        {
            "exp_id": "EXP-017b",
            "phase": PHASE_STABILITY,
            "width": 512,
            "height": 1536,
            "steps": STABILITY_STEPS,
            "results": "docs/evidence/EXP-017/training-runs.jsonl",
        },
    ],
}


def run_one(job: dict, tier: int, dry_run: bool) -> int:
    """One configuration, one fresh OS process."""
    cmd = [
        str(PYTHON),
        "-m",
        "ml.training.train_lora",
        "--exp-id",
        job["exp_id"],
        "--phase",
        job["phase"],
        "--width",
        str(job["width"]),
        "--height",
        str(job["height"]),
        "--steps",
        str(job["steps"]),
        "--tier",
        str(tier),
        "--results",
        job["results"],
    ]
    if dry_run:
        cmd.append("--dry-run")
    print()
    print("=" * 78)
    print(f"  {job['exp_id']}  [{job['phase']}]  {job['width']}x{job['height']}  tier {tier}")
    print("=" * 78)
    return subprocess.run(cmd, cwd=str(REPO)).returncode


def latest_row(results: Path, exp_id: str) -> dict | None:
    if not results.is_file():
        return None
    rows = [r for r in read_jsonl(results) if r.get("exp_id") == exp_id]
    return rows[-1] if rows else None


def project_smoke_duration(results: Path) -> tuple[float, float] | None:
    """Derive s/step and a projected smoke wall-clock from the REAL stability probe.

    The plan forbids starting the smoke run on an estimate that was not measured.
    """
    row = latest_row(results, "EXP-016b")
    if not row or row.get("status") != "ok":
        return None
    per_step = row["resources"].get("seconds_per_optimizer_step")
    if not isinstance(per_step, (int, float)):
        return None
    return float(per_step), float(per_step) * SMOKE_STEPS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=sorted(STAGES), help="which stage to run")
    parser.add_argument("--tier", type=int, default=0)
    parser.add_argument("--plan", action="store_true", help="print the staged plan and exit")
    parser.add_argument("--dry-run", action="store_true", help="pass --dry-run to each runner")
    parser.add_argument(
        "--force-smoke",
        action="store_true",
        help="run the smoke stage even if the projection exceeds the ask threshold "
        "(only after Kylian has approved the projected duration)",
    )
    args = parser.parse_args(argv)

    if args.plan or not args.stage:
        print(json.dumps(STAGES, indent=2))
        print()
        print("Order: 512-probe -> (report projection) -> 512-smoke -> 1536-probe")
        print("The 1536 arm has NO smoke phase by design: feasibility and cost only.")
        return 0

    jobs = STAGES[args.stage]

    if args.stage == "512-smoke" and not args.dry_run:
        results = REPO / "docs" / "evidence" / "EXP-016" / "training-runs.jsonl"
        for gate_id in ("EXP-016a", "EXP-016b"):
            row = latest_row(results, gate_id)
            if not row:
                print(f"REFUSING: {gate_id} has not run. Micro-gates come first.")
                return 2
            if row.get("status") != "ok" or not row.get("gates_passed"):
                print(f"REFUSING: {gate_id} did not pass (status={row.get('status')}).")
                return 2

        projection = project_smoke_duration(results)
        if projection is None:
            print("REFUSING: no measured seconds-per-step from EXP-016b to project from.")
            return 2
        per_step, projected = projection
        print(f"Measured {per_step:.4f} s/step from EXP-016b.")
        print(f"Projected {SMOKE_STEPS} steps -> {projected:.1f} s ({projected / 60:.1f} min).")
        if projected > SMOKE_WALL_ASK_THRESHOLD_SECONDS and not args.force_smoke:
            print()
            print(
                f"STOP: the projection exceeds the {SMOKE_WALL_ASK_THRESHOLD_SECONDS / 60:.0f}-minute "
                "threshold. This needs Kylian's approval before running; re-run with "
                "--force-smoke once approved."
            )
            return 3

    failures = 0
    for job in jobs:
        code = run_one(job, args.tier, args.dry_run)
        if code != 0:
            failures += 1
            print(f"\n{job['exp_id']} returned {code} - recorded as a result, not retried.")
            # A failed probe stops the stage: the next phase is longer, and the
            # tier ladder is walked deliberately rather than by charging ahead.
            break

    print()
    print(f"stage {args.stage}: {len(jobs) - failures} of {len(jobs)} jobs ok")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
