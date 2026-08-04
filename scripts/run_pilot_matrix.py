"""Run the capped Prototype 4 pilot review matrix, one process per checkpoint.

Six trained arms x two checkpoints x eight images, plus one base SD 1.5 arm per
style at the identical prompt text. The total is asserted against
`style_kit.PILOT_MATRIX_MAX_GENERATIONS` BEFORE anything runs, so the matrix
cannot quietly grow past what the plan approved.

Run:
    .venv/Scripts/python.exe scripts/run_pilot_matrix.py --plan
    .venv/Scripts/python.exe scripts/run_pilot_matrix.py
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.training import style_kit  # noqa: E402

PYTHON = REPO / ".venv" / "Scripts" / "python.exe"
LORA_ROOT = REPO / "outputs" / "lora"

# arm id -> (style, run slug prefix). The slug is how train_lora named the run.
ARMS: list[tuple[str, str]] = [
    ("EXP-020", "minimal-geometric"),
    ("EXP-021", "ukiyo-e"),
    ("EXP-022", "retro-poster"),
    ("EXP-023", "minimal-geometric"),
    ("EXP-024n12", "minimal-geometric"),
    ("EXP-024n24", "minimal-geometric"),
]


def checkpoint_dirs(arm: str) -> list[tuple[int, Path]]:
    matches = sorted(LORA_ROOT.glob(f"{arm}__*"))
    if not matches:
        return []
    found = []
    for step in style_kit.PILOT_CHECKPOINT_STEPS:
        path = matches[0] / f"step{step:05d}"
        if path.is_dir():
            found.append((step, path))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true", help="print the matrix and exit")
    args = parser.parse_args(argv)

    per_checkpoint = (
        len(style_kit.PILOT_PROMPTS) * len(style_kit.PILOT_SEEDS) * len(style_kit.PILOT_LORA_WEIGHTS)
    )
    jobs: list[tuple[str, str, int, str]] = []
    for arm, style in ARMS:
        for step, path in checkpoint_dirs(arm):
            jobs.append((arm, style, step, str(path.relative_to(REPO)).replace("\\", "/")))

    base_jobs = [(f"BASE-{s}", s) for s in style_kit.STYLE_ORDER]
    base_images = len(style_kit.PILOT_PROMPTS) * len(style_kit.PILOT_SEEDS)
    total = len(jobs) * per_checkpoint + len(base_jobs) * base_images

    print(f"trained arms:   {len(jobs)} checkpoint jobs x {per_checkpoint} images")
    print(f"base reference: {len(base_jobs)} jobs x {base_images} images")
    print(f"TOTAL:          {total} generations (cap {style_kit.PILOT_MATRIX_MAX_GENERATIONS})")

    if total > style_kit.PILOT_MATRIX_MAX_GENERATIONS:
        print("REFUSING: the pilot matrix exceeds its declared cap.")
        return 2

    if args.plan:
        for arm, style, step, path in jobs:
            print(f"  {arm:12s} {style:18s} step {step:5d}  {path}")
        for arm, style in base_jobs:
            print(f"  {arm:12s} {style:18s} base SD 1.5 (no adapter)")
        return 0

    failures = 0
    for arm, style, step, path in jobs:
        cmd = [
            str(PYTHON), "-m", "ml.training.validate_style",
            "--arm", arm, "--style", style,
            "--checkpoint-dir", path, "--checkpoint-step", str(step),
        ]
        if subprocess.run(cmd, cwd=str(REPO)).returncode != 0:
            failures += 1
            print(f"{arm} step {step} FAILED - recorded, not retried")
            break

    if not failures:
        for arm, style in base_jobs:
            cmd = [
                str(PYTHON), "-m", "ml.training.validate_style",
                "--arm", arm, "--style", style,
            ]
            if subprocess.run(cmd, cwd=str(REPO)).returncode != 0:
                failures += 1
                break

    print()
    print(f"pilot matrix: {'complete' if not failures else 'INCOMPLETE'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
