"""EXP-035 - can the neutral placeholder influence a prompt-only generation?

WHY THIS HAS TO BE MEASURED. With IP-Adapter resident, diffusers 0.39.0 sets
`added_cond_kwargs = None` when no reference is passed
(`pipeline_stable_diffusion.py:1014-1018`) and the UNet then RAISES, because
`encoder_hid_dim_type == "ip_image_proj"` requires `image_embeds`
(`unet_2d_condition.py:964-967`). A prompt-only request therefore CANNOT simply
omit the image. The service keeps the adapter resident at scale 0.0 and passes a
constructed mid-grey placeholder instead.

That design rests on a claim: at scale 0.0 the reference cannot affect the
result. M4 measured the neighbouring fact - 12/12 IP-Adapter runs at scale 0.0
were byte-identical to the text-only baseline - but it did so with REAL
reference images and no LoRA loaded. This experiment tests the claim directly in
the configuration the service actually runs.

METHOD. Two generations, identical in every respect except the reference image,
both at scale 0.0, both matching EXP-034's case 1 exactly (minimal-geometric,
"a mountain and a rising sun", seed 42, weight 0.7, 512x1536):

  1. the mid-grey placeholder the service itself constructs
  2. R2 - a real, completely different image, from the HOLDOUT split

PASS CONDITION, DECLARED BEFORE RUNNING: both outputs are byte-identical to each
other AND to EXP-034's prompt-only case-1 output, whose hash is read from the
recorded evidence rather than transcribed.

STATED LIMITATION. A pass shows the reference CONTENT cannot influence the
output at scale 0.0 in this stack. It does NOT re-establish equivalence to the
frozen text-only baseline: that stack has no LoRA and a different prompt, so the
two are not comparable at fixed settings, and the text-only claim continues to
rest on M4's separate measurement.

Run:
    .venv/Scripts/python.exe scripts/measure_reference_neutralisation.py
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from apps.api.pipeline import (  # noqa: E402
    NEUTRAL_REFERENCE_LEVEL,
    NEUTRAL_REFERENCE_SIZE,
    ResidentPipeline,
    neutral_reference,
)
from ml.inference.reference_schema import REFERENCES  # noqa: E402

EXP_ID = "EXP-035"

STYLE = "minimal-geometric"
SUBJECT = "a mountain and a rising sun"
SEED = 42
LORA_WEIGHT = 0.7
SCALE = 0.0

OUTPUT_ROOT = REPO / "outputs" / EXP_ID
RESULTS_PATH = REPO / "docs" / "evidence" / EXP_ID / "neutralisation.json"
EXP_034_ROWS = REPO / "docs" / "evidence" / "EXP-034" / "service-residency.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def exp_034_reference_hash() -> str | None:
    """The prompt-only case-1 hash from EXP-034, read rather than transcribed."""
    if not EXP_034_ROWS.is_file():
        return None
    for line in EXP_034_ROWS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if (
            row.get("style") == STYLE
            and row.get("reference_present") is False
            and row.get("seed") == SEED
            and row.get("status") == "ok"
        ):
            return row.get("image_sha256")
    return None


def main() -> int:
    from PIL import Image

    r2 = REFERENCES["R2"]
    r2_path = REPO / r2.repo_path
    if not r2_path.is_file():
        print(f"reference R2 missing at {r2.repo_path}")
        return 2

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(r2_path) as raw:
        r2_image = raw.convert("RGB")

    arms = [
        ("neutral-placeholder", neutral_reference(),
         f"the service's own constructed {NEUTRAL_REFERENCE_SIZE}px "
         f"level-{NEUTRAL_REFERENCE_LEVEL} grey"),
        ("holdout-R2", r2_image,
         f"R2, real artwork from the holdout split, {r2.width}x{r2.height}"),
    ]

    print(f"{EXP_ID}: does the reference content matter at IP-Adapter scale {SCALE}?")
    print(f"  style {STYLE}, subject {SUBJECT!r}, seed {SEED}, weight {LORA_WEIGHT}")
    print()

    pipeline = ResidentPipeline(REPO)
    results = []
    started = time.perf_counter()

    for name, image, description in arms:
        print(f"  {name:<22} ... ", end="", flush=True)
        outcome = pipeline.generate(
            style_key=STYLE,
            subject_prompt=SUBJECT,
            seed=SEED,
            lora_weight=LORA_WEIGHT,
            ip_adapter_scale=SCALE,
            reference_image=image,
            deadline_seconds=None,
        )
        filename = f"{EXP_ID}__{name}__scale0__seed{SEED}.png"
        (OUTPUT_ROOT / filename).write_bytes(outcome.image_png)
        results.append(
            {
                "arm": name,
                "description": description,
                "image_sha256": outcome.image_sha256,
                "ip_adapter_scale_applied": outcome.ip_adapter_scale_applied,
                "active_adapters": list(outcome.active_adapters),
                "generate_seconds": outcome.generate_seconds,
                "output_path": f"outputs/{EXP_ID}/{filename}",
            }
        )
        print(f"ok  {outcome.generate_seconds}s  sha {outcome.image_sha256[:16]}")

    hashes = {row["image_sha256"] for row in results}
    arms_identical = len(hashes) == 1

    baseline = exp_034_reference_hash()
    matches_baseline = baseline is not None and hashes == {baseline}

    passed = arms_identical and matches_baseline
    report = {
        "exp_id": EXP_ID,
        "timestamp_utc": utc_now(),
        "style": STYLE,
        "subject": SUBJECT,
        "seed": SEED,
        "lora_weight": LORA_WEIGHT,
        "ip_adapter_scale": SCALE,
        "wall_seconds": round(time.perf_counter() - started, 2),
        "arms": results,
        "exp_034_prompt_only_sha256": baseline,
        "arms_byte_identical": arms_identical,
        "matches_exp_034_prompt_only": matches_baseline,
        "passed": passed,
        "limitation": (
            "Shows that the reference CONTENT cannot influence the output at scale 0.0 in "
            "this stack. Does NOT re-establish equivalence to the frozen text-only baseline, "
            "which has no LoRA and a different prompt and is therefore not comparable at "
            "fixed settings; that claim continues to rest on M4's separate 12/12 result."
        ),
    }
    RESULTS_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    print()
    print(f"  the two arms are byte-identical to each other : {arms_identical}")
    print(f"  and identical to EXP-034's prompt-only output : {matches_baseline}")
    if baseline:
        print(f"  EXP-034 reference hash: {baseline[:16]}...")
    print()
    print(f"  {EXP_ID}: {'PASS' if passed else 'FAILED'}")
    if not passed:
        print("  A difference here means the placeholder is NOT neutral and the")
        print("  prompt-only path is carrying reference information. Stop and report.")
    print(f"  report -> {RESULTS_PATH.relative_to(REPO)}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
