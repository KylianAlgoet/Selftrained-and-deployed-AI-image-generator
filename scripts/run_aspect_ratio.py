"""Orchestrate EXP-005: one aspect-ratio strategy per fresh OS process.

The first EXP-005 run (2026-07-30) executed all four geometries in a single
process and produced two contaminated measurements. Recorded honestly rather than
quietly re-run, because the contamination is itself a methodological finding:

  * `peak_vram_reserved_mb` and `peak_device_used_mb` became monotonic
    high-water marks of the caching allocator's pool, not per-geometry
    requirements. `torch.cuda.reset_peak_memory_stats()` resets the peak
    counters but does not return the pool, so after 512x1536 the 512x512
    strategy reported the 1536 geometry's 5762/6875 MiB figures.
  * Wall-clock time for `square-crop` (identical 512x512 work to `direct-1x1`)
    came out at 7.96s median vs 4.98s. Thermal throttling was tested and ruled
    out: on a hotter, more throttled card (2250->1965 MHz, 75C) the same work
    ran at 4.10s median, i.e. FASTER. The residual difference is in-process
    allocator state, not a property of the strategy.

`peak_vram_allocated_mb` was unaffected (2675.38 MiB for both), which is what
proved the two strategies do identical work and made the artefact visible.

Fix: one strategy per process, mirroring what the model benchmark already does
per candidate.

Run:
    .venv/Scripts/python.exe scripts/run_aspect_ratio.py
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.inference.aspect_ratio import EXP_ID, STRATEGIES  # noqa: E402
from ml.inference.bench_schema import (  # noqa: E402
    MODELS,
    STATUS_OK,
    read_jsonl,
    render_summary_markdown,
    summarize,
    write_csv,
)

PYTHON = REPO / ".venv" / "Scripts" / "python.exe"
EVIDENCE = REPO / "docs" / "evidence" / EXP_ID


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EXP-005 orchestrator (one process per strategy)")
    parser.add_argument("--model", default="sd15", choices=sorted(MODELS))
    args = parser.parse_args(argv)

    spec = MODELS[args.model]
    jsonl_path = EVIDENCE / f"results-{spec.slug}.jsonl"
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if jsonl_path.exists():
        jsonl_path.unlink()

    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    for index, (strategy, _resolution) in enumerate(STRATEGIES):
        print(f"\n{'=' * 78}\nFRESH PROCESS: {strategy}\n{'=' * 78}", flush=True)
        command = [
            str(PYTHON), "-m", "ml.inference.aspect_ratio",
            "--model", args.model,
            "--strategy", strategy,
        ]
        if index > 0:
            command.append("--append")
        completed = subprocess.run(command, cwd=REPO, env=env)
        print(f"--- {strategy} exited with code {completed.returncode}", flush=True)

    rows = read_jsonl(jsonl_path)
    if not rows:
        print("no results collected", file=sys.stderr)
        return 1
    write_csv(rows, EVIDENCE / f"results-{spec.slug}.csv")
    (EVIDENCE / f"summary-{spec.slug}.md").write_text(
        render_summary_markdown(
            summarize(rows), f"{EXP_ID} aspect-ratio measurements - {spec.repo_id} (UNSCORED)"
        ),
        encoding="utf-8",
    )
    build_sheet(rows, spec)

    ok = sum(1 for r in rows if r["status"] == STATUS_OK)
    print(f"\n{ok}/{len(rows)} runs ok. Evidence: {EVIDENCE}")
    print("Each strategy measured in its own process - memory and timing figures are uncontaminated.")
    return 0


def build_sheet(rows: list[dict], spec) -> None:
    """One row per strategy at a fixed seed, so the geometries can be compared
    side by side. Mixed aspect ratios are centred in equal cells on purpose -
    the differing shapes are the point of the comparison."""
    from ml.dataset.contact_sheet import make_contact_sheet
    from ml.evaluation import prompt_kit

    fixed_seed = prompt_kit.SEEDS[0]
    prompt_ids = ["P4-deck", "P1-poster"]
    paths = []
    for strategy, _res in STRATEGIES:
        for prompt_id in prompt_ids:
            match = [
                r for r in rows
                if r["status"] == STATUS_OK
                and r["track"] == strategy
                and r["prompt_id"] == prompt_id
                and int(r["seed"]) == fixed_seed
                and r.get("output_path")
            ]
            if match:
                candidate = REPO / match[0]["output_path"]
                if candidate.exists():
                    paths.append(candidate)
    if not paths:
        print("  no successful outputs - no aspect-ratio sheet built")
        return
    out = EVIDENCE / f"aspect-ratio-comparison-seed{fixed_seed}.jpg"
    make_contact_sheet(paths, out, thumb_size=256, columns=len(prompt_ids))
    print(f"  contact sheet: {out.name} ({out.stat().st_size // 1024} KB, {len(paths)} images)")


if __name__ == "__main__":
    sys.exit(main())
