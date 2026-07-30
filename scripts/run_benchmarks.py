"""Orchestrate the Prototype 1 benchmark: one candidate per fresh OS process.

Why subprocesses rather than a loop inside one process: VRAM is only reliably
returned to the driver when the process exits. Benchmarking SDXL after SD 1.5 in
the same process would measure SDXL against a polluted allocator state, and an
OOM in one candidate could poison the next. Each candidate therefore gets a
clean process, and a crash in one does not lose the others' results.

Produces, after the per-model runs:
  - a combined results CSV across all candidates
  - Track A and Track B cross-model contact sheets (fixed seed, all prompts)
  - an UNSCORED measurement summary for the human-review gate

Run:
    .venv/Scripts/python.exe scripts/run_benchmarks.py
    .venv/Scripts/python.exe scripts/run_benchmarks.py --models sd15,sdxl
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.evaluation import prompt_kit  # noqa: E402
from ml.inference.bench_schema import (  # noqa: E402
    MODELS,
    STATUS_OK,
    read_jsonl,
    render_summary_markdown,
    summarize,
    write_csv,
)

PYTHON = REPO / ".venv" / "Scripts" / "python.exe"
EVIDENCE = REPO / "docs" / "evidence"
OUTPUTS = REPO / "outputs"

# One experiment id per candidate, so registry rows map 1:1 to runs.
EXPERIMENTS: dict[str, str] = {
    "sd15": "EXP-002",
    "sd21base": "EXP-003",
    "sdxl": "EXP-004",
}

COMBINED_DIR = EVIDENCE / "prototype-1"


def run_one(model_key: str, probes: bool) -> int:
    exp_id = EXPERIMENTS[model_key]
    command = [
        str(PYTHON), "-m", "ml.inference.benchmark",
        "--model", model_key,
        "--exp", exp_id,
    ]
    if probes:
        command.append("--probes")
    print(f"\n{'=' * 78}\nSPAWNING fresh process: {model_key} -> {exp_id}\n{'=' * 78}", flush=True)
    completed = subprocess.run(command, cwd=REPO, env={"PYTHONIOENCODING": "utf-8", **_env()})
    print(f"--- {model_key} exited with code {completed.returncode}", flush=True)
    return completed.returncode


def _env() -> dict:
    import os

    return dict(os.environ)


def collect_rows(model_keys: list[str]) -> list[dict]:
    rows: list[dict] = []
    for key in model_keys:
        spec = MODELS[key]
        path = EVIDENCE / EXPERIMENTS[key] / f"results-{spec.slug}.jsonl"
        if path.exists():
            rows += read_jsonl(path)
        else:
            print(f"  (no results file for {key} at {path})")
    return rows


def build_cross_model_sheets(rows: list[dict], model_keys: list[str]) -> list[Path]:
    """One sheet per track: rows = candidates, columns = the 5 frozen prompts,
    at a single fixed seed so the comparison is apples-to-apples."""
    from ml.dataset.contact_sheet import make_contact_sheet

    COMBINED_DIR.mkdir(parents=True, exist_ok=True)
    fixed_seed = prompt_kit.SEEDS[0]
    prompt_order = [p.id for p in prompt_kit.PROMPTS]
    sheets: list[Path] = []

    for track in ("A", "B"):
        paths: list[Path] = []
        for key in model_keys:
            spec = MODELS[key]
            # A candidate whose native resolution IS the Track A resolution has no
            # separate Track B run. Its Track A images *are* its native-resolution
            # images, so they belong in the Track B sheet - otherwise the sheet
            # shows only the larger models and defeats the purpose of Track B,
            # which exists precisely so each model is judged at its own size.
            source_track = track
            expected_resolution: tuple[int, int] | None = None
            if track == "B":
                expected_resolution = spec.track_b_resolution
                if spec.track_b_resolution == prompt_kit.TRACK_A_RESOLUTION:
                    source_track = "A"

            for prompt_id in prompt_order:
                match = [
                    r for r in rows
                    if r["status"] == STATUS_OK
                    and r["model_repo_id"] == spec.repo_id
                    and r["track"] == source_track
                    and r["prompt_id"] == prompt_id
                    and int(r["seed"]) == fixed_seed
                    and (
                        expected_resolution is None
                        or (int(r["width"]), int(r["height"])) == expected_resolution
                    )
                ]
                if match:
                    candidate = REPO / match[0]["output_path"]
                    if candidate.exists():
                        paths.append(candidate)
        if not paths:
            print(f"  no successful Track {track} outputs at seed {fixed_seed} - no sheet built")
            continue
        out = COMBINED_DIR / f"cross-model-track-{track}-seed{fixed_seed}.jpg"
        make_contact_sheet(paths, out, thumb_size=256, columns=len(prompt_order))
        size_kb = out.stat().st_size // 1024
        print(f"  contact sheet: {out.name} ({size_kb} KB, {len(paths)} images)")
        sheets.append(out)
    return sheets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prototype 1 benchmark orchestrator")
    parser.add_argument("--models", default="sd15,sd21base,sdxl", help="comma-separated candidate keys, in order")
    parser.add_argument("--probes", action="store_true", help="include out-of-distribution resolution probes")
    parser.add_argument("--collect-only", action="store_true", help="skip running; just aggregate existing results")
    args = parser.parse_args(argv)

    model_keys = [k.strip() for k in args.models.split(",") if k.strip()]
    unknown = [k for k in model_keys if k not in MODELS]
    if unknown:
        print(f"unknown candidate keys: {unknown}; known: {sorted(MODELS)}", file=sys.stderr)
        return 2

    print(f"frozen kit fingerprint: {prompt_kit.kit_fingerprint()}")

    if not args.collect_only:
        for key in model_keys:
            # A non-zero exit is recorded and the run continues: one infeasible
            # candidate is a legitimate RQ2 result, not a reason to abandon M3.
            run_one(key, args.probes)

    print(f"\n{'=' * 78}\nAGGREGATING\n{'=' * 78}")
    rows = collect_rows(model_keys)
    if not rows:
        print("no results collected")
        return 1

    COMBINED_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(rows, COMBINED_DIR / "results-all-candidates.csv")
    summaries = summarize(rows)
    (COMBINED_DIR / "measurement-summary.md").write_text(
        render_summary_markdown(summaries, "Prototype 1 - cross-candidate measurements (UNSCORED)"),
        encoding="utf-8",
    )
    build_cross_model_sheets(rows, model_keys)

    ok = sum(1 for r in rows if r["status"] == STATUS_OK)
    print(f"\n{ok}/{len(rows)} runs ok across {len(model_keys)} candidates")
    print(f"combined evidence: {COMBINED_DIR}")
    print("\nMeasurements only - no quality verdict. Rubric scoring happens at the human-review gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
