"""Orchestrate the Prototype 2 Phase-1 experiments across process boundaries.

THE POINT OF THIS SCRIPT IS THE PROCESS BOUNDARY. Carrying forward the EXP-005
allocator-contamination finding, a fresh OS process is launched for every distinct

    method x adapter variant x output resolution x memory tier

and this script is what actually launches them, as real subprocesses. Nothing here
imports torch: if it did, this parent process would hold CUDA context while its
children measured, which is the contamination it exists to prevent.

Influence levels deliberately SHARE a process within one such combination, because
tensor geometry does not change across levels and reloading SD 1.5 per level would
multiply runtime for no measurement gain. That sharing is declared, not hidden, and
carries three obligations:

  * `peak_vram_allocated_mb` is per-run and is the level-to-level figure;
  * `peak_vram_reserved_mb` / `peak_device_used_mb` are process-level high-water
    marks and are never compared between levels sharing a process;
  * the clean-process spot checks (EXP-008b, EXP-009b) must pass at the
    pre-declared 2 % tolerance before the shared-process comparison is accepted.

Run everything:
    .venv/Scripts/python.exe scripts/run_reference_conditioning.py

Run one stage:
    .venv/Scripts/python.exe scripts/run_reference_conditioning.py --only EXP-009
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

PYTHON = REPO / ".venv" / "Scripts" / "python.exe"
EVIDENCE = REPO / "docs" / "evidence"

SWEEP_CONDITIONS = "C1,C2,C3,C4"
STRESS_CONDITIONS = "C5,C6"
DECK_CONDITIONS = "C1,C2,C4"

# Sweep points and named levels run in ONE shared process per method. They are
# different numbers by design (img2img sweeps 0.90..0.30 while its named levels
# are 0.85/0.65/0.40), and the spot check re-runs the NAMED levels - so without
# both here, the clean-process runs would have nothing to be compared against.
SWEEP_AND_NAMED = "sweep,weak,medium,strong"


@dataclass
class Stage:
    """One fresh OS process."""

    exp_id: str
    method: str
    conditions: str
    levels: str
    width: int = 512
    height: int = 512
    seeds: str = ""
    suffix: str = ""
    note: str = ""
    extra: list[str] = field(default_factory=list)

    def command(self) -> list[str]:
        cmd = [
            str(PYTHON), "-m", "ml.inference.reference_conditioning",
            "--exp", self.exp_id,
            "--method", self.method,
            "--conditions", self.conditions,
            "--levels", self.levels,
            "--width", str(self.width),
            "--height", str(self.height),
        ]
        if self.seeds:
            cmd += ["--seeds", self.seeds]
        if self.suffix:
            cmd += ["--suffix", self.suffix]
        return cmd + self.extra


def build_plan() -> list[Stage]:
    """The experiment plan, one Stage per process.

    Deviation from the plan's run counts, recorded rather than silent: EXP-008 and
    EXP-009 run the three NAMED levels across the full condition grid in addition
    to the five sweep points, not only at the spot-check cell. Two reasons, both
    measurement-driven: the clean-process spot check needs a shared-process
    counterpart at exactly those values, and the method-comparison and multi-seed
    contact sheets need `medium` for every condition and seed so
    `diversity_across_seeds` is finally scoreable on a like-for-like grid.
    """
    stages: list[Stage] = []

    # --- EXP-008 / EXP-009: the two strength sweeps, one shared process each ---
    for exp_id, method in (("EXP-008", "img2img"), ("EXP-009", "ip-adapter")):
        stages.append(
            Stage(
                exp_id=exp_id,
                method=method,
                conditions=SWEEP_CONDITIONS,
                levels=SWEEP_AND_NAMED,
                note=f"{method} strength sweep, shared process across levels",
            )
        )

        # --- EXP-008b / EXP-009b: clean-process spot checks, ONE LEVEL PER
        # PROCESS. Fixed at C1/seed 42 so each has an exact shared-process twin.
        for level in ("weak", "medium", "strong"):
            stages.append(
                Stage(
                    exp_id=f"{exp_id}b",
                    method=method,
                    conditions="C1",
                    levels=level,
                    seeds="42",
                    suffix=f"clean-{level}",
                    note=f"clean-process spot check, {level} only, its own process",
                )
            )

    # --- EXP-010: lower-bound equivalence diagnostic ---------------------------
    # The text-only baseline, and IP-Adapter at scale 0.0. Two processes: the
    # baseline must be measured with NO adapter and NO encoder resident, which is
    # precisely what makes its VRAM figure meaningful.
    stages.append(
        Stage(
            exp_id="EXP-010", method="text-only", conditions=SWEEP_CONDITIONS, levels="none",
            note="text-only baseline; no adapter, no image encoder in this process",
        )
    )
    stages.append(
        Stage(
            exp_id="EXP-010", method="ip-adapter", conditions=SWEEP_CONDITIONS, levels="none",
            suffix="scale-zero",
            note="IP-Adapter at scale 0.0 - the lower-bound DIAGNOSTIC, not a pass/fail condition",
        )
    )

    # The deck format needs its own text-only baseline, in its own process: a
    # 512x512 baseline cannot serve a 512x1536 output, so without this every
    # EXP-013 row would carry an empty `similarity_to_baseline` for no reason
    # other than a missing run.
    stages.append(
        Stage(
            exp_id="EXP-010", method="text-only", conditions=DECK_CONDITIONS, levels="none",
            width=512, height=1536, suffix="deck",
            note="text-only baseline at the deck format, so EXP-013 has one to be compared against",
        )
    )

    # --- EXP-011: conflict (C5) and difficult reference (C6) ------------------
    for method in ("img2img", "ip-adapter"):
        stages.append(
            Stage(
                exp_id="EXP-011", method=method, conditions=STRESS_CONDITIONS,
                levels="weak,medium,strong",
                note="conflict and difficult reference; prompt loss here is the measurement",
            )
        )

    # --- EXP-012: the IP-Adapter-Plus within-method variant --------------------
    # Its own process: a different adapter variant is a different process by the
    # boundary rule, and its VRAM must not be read off IP-Adapter's high-water mark.
    stages.append(
        Stage(
            exp_id="EXP-012", method="ip-adapter-plus", conditions=SWEEP_CONDITIONS,
            levels="medium", note="Plus variant, medium level only; first item dropped under scope reduction",
        )
    )

    # --- EXP-013: the deck format ---------------------------------------------
    # A different output resolution is a different process by the boundary rule.
    for method in ("img2img", "ip-adapter"):
        stages.append(
            Stage(
                exp_id="EXP-013", method=method, conditions=DECK_CONDITIONS, levels="medium",
                width=512, height=1536,
                note="DR-007 deck format; img2img must crop the reference to 1:3, IP-Adapter need not",
            )
        )

    return stages


def run_stage(stage: Stage, index: int, total: int) -> dict:
    label = f"{stage.exp_id} {stage.method} {stage.width}x{stage.height}"
    if stage.suffix:
        label += f" [{stage.suffix}]"
    print(f"\n{'=' * 78}\n[{index}/{total}] {label}\n  {stage.note}\n{'=' * 78}", flush=True)

    started = time.perf_counter()
    completed = subprocess.run(stage.command(), cwd=REPO)
    elapsed = round(time.perf_counter() - started, 2)

    print(f"  -> exit {completed.returncode} in {elapsed}s", flush=True)
    return {
        "exp_id": stage.exp_id,
        "method": stage.method,
        "conditions": stage.conditions,
        "levels": stage.levels,
        "width": stage.width,
        "height": stage.height,
        "seeds": stage.seeds or "frozen kit seeds",
        "suffix": stage.suffix,
        "note": stage.note,
        "command": " ".join(stage.command()[1:]),
        "exit_code": completed.returncode,
        "wall_seconds": elapsed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", default="", help="run one experiment id, e.g. EXP-009")
    parser.add_argument(
        "--start-at", type=int, default=1,
        help="resume from this 1-based stage number after an interrupted run. Each stage is a "
             "self-contained process that rewrites its own results file, so resuming repeats no "
             "completed stage and leaves no half-written one behind.",
    )
    parser.add_argument("--dry-run", action="store_true", help="print the plan without running it")
    args = parser.parse_args(argv)

    if not PYTHON.exists():
        print(f"interpreter not found at {PYTHON}", file=sys.stderr)
        return 2

    stages = build_plan()
    if args.only:
        stages = [s for s in stages if s.exp_id == args.only]
        if not stages:
            print(f"no stage matches {args.only!r}", file=sys.stderr)
            return 2
    if args.start_at > 1:
        if args.start_at > len(stages):
            print(f"--start-at {args.start_at} is beyond the {len(stages)} planned stages",
                  file=sys.stderr)
            return 2
        skipped = stages[: args.start_at - 1]
        stages = stages[args.start_at - 1:]
        print(f"resuming at stage {args.start_at}; skipping {len(skipped)} already-completed "
              f"stage(s): {', '.join(sorted({s.exp_id for s in skipped}))}")

    if args.dry_run:
        for index, stage in enumerate(stages, start=1):
            print(f"[{index}/{len(stages)}] {' '.join(stage.command()[1:])}")
        print(f"\n{len(stages)} processes planned")
        return 0

    started = datetime.now(timezone.utc)
    records = [run_stage(stage, i, len(stages)) for i, stage in enumerate(stages, start=1)]
    finished = datetime.now(timezone.utc)

    failed = [r for r in records if r["exit_code"] != 0]
    manifest = {
        "started_utc": started.isoformat(timespec="seconds"),
        "finished_utc": finished.isoformat(timespec="seconds"),
        "total_wall_seconds": round((finished - started).total_seconds(), 2),
        "processes_launched": len(records),
        "processes_failed": len(failed),
        "resumed_from_stage": args.start_at,
        "stages_covered_by_this_manifest": (
            "all planned stages" if args.start_at == 1 else
            f"stages {args.start_at} onward only; earlier stages ran in an interrupted "
            "invocation and are documented by their own results files"
        ),
        "process_boundary": "one fresh OS process per method x adapter variant x resolution x memory tier",
        "levels_share_a_process": True,
        "stages": records,
    }
    out = EVIDENCE / "prototype-2" / "process-run-manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"\n{'=' * 78}")
    print(f"{len(records) - len(failed)}/{len(records)} processes exited 0 in {manifest['total_wall_seconds']}s")
    for record in failed:
        print(f"  FAILED: {record['exp_id']} {record['method']} -> exit {record['exit_code']}")
    print(f"manifest: {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
