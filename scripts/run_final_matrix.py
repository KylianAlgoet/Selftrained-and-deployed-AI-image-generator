"""Launch the EXP-031 final validation matrix, one arm per fresh OS process.

The cap is asserted BEFORE the first image, not tallied afterwards - a matrix that
only discovers it overran once it has overrun is not capped. Adapters come only
from the gate-1 approved candidate set in `ml.training.final_matrix.CANDIDATES`.

Run:
    .venv/Scripts/python.exe scripts/run_final_matrix.py [--dry-run]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.training import final_matrix as fm  # noqa: E402
from ml.training import style_kit  # noqa: E402

PYTHON = REPO / ".venv" / "Scripts" / "python.exe"


def adapter_dir_for(exp_id: str, step: int) -> Path:
    path = REPO / "docs" / "evidence" / exp_id / "training-runs.jsonl"
    row = json.loads(path.open(encoding="utf-8").readline())
    final = Path(row["adapter"]["path"])
    return REPO / final.parent.parent / f"step{step:05d}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    total = fm.planned_generations()
    cap = style_kit.FINAL_MATRIX_MAX_GENERATIONS
    print(f"planned {total} generations against a cap of {cap}")
    if total > cap:
        print(f"REFUSED: {total} exceeds the pre-declared cap of {cap}")
        return 1
    print(f"matrix fingerprint {fm.matrix_fingerprint()}")

    arms = fm.planned_arms()
    print(f"{len(arms)} arms, one OS process each\n")

    failures = []
    for n, arm in enumerate(arms, start=1):
        cmd = [
            str(PYTHON), "-m", "ml.training.final_matrix",
            "--kind", arm["kind"], "--arm", arm["arm"], "--style", arm["style"],
            "--checkpoint-step", str(arm["checkpoint_step"]),
            "--geometry", arm["geometry"],
        ]
        if arm["kind"] != "base":
            exp_id = arm["arm"]
            cmd += ["--checkpoint-dir", str(adapter_dir_for(exp_id, arm["checkpoint_step"]))]
        if args.dry_run:
            cmd.append("--plan-only")

        label = f"[{n}/{len(arms)}] {arm['arm']} {arm['style']} ck{arm['checkpoint_step']} {arm['geometry']}"
        print(label)
        result = subprocess.run(cmd, cwd=str(REPO))
        if result.returncode != 0:
            failures.append(label)
            print(f"  FAILED rc={result.returncode}")

    print()
    if failures:
        print(f"{len(failures)} arms failed:")
        for f in failures:
            print(f"  {f}")
        return 1
    print("all arms completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
