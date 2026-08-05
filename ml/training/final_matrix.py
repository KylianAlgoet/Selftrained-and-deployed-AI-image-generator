"""EXP-031 Phase 1 - the Prototype 4 FINAL VALIDATION MATRIX (generation only).

Runs ONLY on checkpoints Kylian approved at gate 1: the three 600-step per-style
full runs (EXP-027/028/029) at steps 300 and 600, the balanced multi-style run
(EXP-030), and the untrained SD 1.5 control. Rejected pilot checkpoints are never
generated for.

**Why the prompts live here and not in `style_kit`.** The style kit is hash-locked
at `fc11d828...` and every Phase-A row records that fingerprint. Adding the final
prompts to it would move the fingerprint and split the milestone's evidence across
two kit versions for no gain. The kit froze the PILOT configuration; this module
freezes the FINAL matrix, carries its own fingerprint, and leaves the kit exactly
as Phase A recorded it.

**Cap.** `style_kit.FINAL_MATRIX_MAX_GENERATIONS` is 432, declared before any
Phase-B execution. `planned_generations()` computes the exact total and the
orchestrator asserts it against the cap BEFORE the first image, so the matrix
cannot quietly grow while it runs.

Phase 1 only: this module generates and records what it can read back from the
live pipeline. It computes NO similarity indicator and imports no metric encoder;
that is Phase 2 (`scripts/evaluate_p4_memorisation.py`).

**No visual-quality judgement is made here.** Gate 2 is a human gate.
"""

import argparse
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ml.dataset.captions import STYLE_PHRASES  # noqa: E402
from ml.evaluation import prompt_kit  # noqa: E402
from ml.training import style_kit  # noqa: E402
from ml.training.lora_schema import BASE_MODEL_REPO_ID, BASE_MODEL_REVISION  # noqa: E402

MIB = 1024**2
OUTPUT_ROOT = REPO / "outputs" / "EXP-031"
RESULTS = REPO / "docs" / "evidence" / "EXP-031" / "final-matrix.jsonl"


@dataclass(frozen=True)
class FinalPrompt:
    id: str
    role: str
    template: str
    intent: str


# Four roles, as the approved plan required. `{trigger}` and `{phrase}` are
# substituted per style; FP4 deliberately contains neither.
FINAL_PROMPTS: tuple[FinalPrompt, ...] = (
    FinalPrompt(
        id="FP1-style",
        role="style-matching",
        template="{trigger} {phrase} skateboard decal artwork, a coiled serpent",
        intent="does the trigger produce the trained style on a subject the style can carry",
    ),
    FinalPrompt(
        id="FP2-shared",
        role="shared-cross-style",
        template="{trigger} {phrase} skateboard decal artwork, a mountain and a rising sun",
        intent="identical subject across all three styles, isolating the LoRA from the prompt",
    ),
    FinalPrompt(
        id="FP3-out-of-style",
        role="out-of-style",
        template="{trigger} {phrase} skateboard decal artwork, a photorealistic city street at night",
        intent="a subject the style does not naturally carry; probes prompt authority under the LoRA",
    ),
    FinalPrompt(
        id="FP4-style-free",
        role="style-free",
        template="skateboard decal artwork, a coiled serpent",
        intent=(
            "NO trigger and NO style phrase - does the adapter leak into prompts that never "
            "asked for it, which a style LoRA should not do"
        ),
    ),
)

# Blocks, each with a stated decision it serves. Sizes are computed, never counted
# by hand.
WEIGHTS_SWEEP = style_kit.FINAL_LORA_WEIGHTS          # 0.0 / 0.4 / 0.7 / 1.0
SEEDS_SWEEP = style_kit.FINAL_SEEDS[:2]               # 42 / 1337
SEEDS_FULL = style_kit.FINAL_SEEDS                    # 42 / 1337 / 2026
WEIGHT_NOMINAL = 0.7
WEIGHTS_DECK = (0.7, 1.0)

BLOCK_A_PROMPTS = ("FP1-style", "FP2-shared")
BLOCK_B_PROMPTS = tuple(p.id for p in FINAL_PROMPTS)

# The approved candidate set. Nothing else is generated for.
CANDIDATES: tuple[tuple[str, str, int], ...] = (
    ("EXP-027", "minimal-geometric", 300),
    ("EXP-027", "minimal-geometric", 600),
    ("EXP-028", "ukiyo-e", 300),
    ("EXP-028", "ukiyo-e", 600),
    ("EXP-029", "retro-poster", 300),
    ("EXP-029", "retro-poster", 600),
)
MULTI_STYLE_ARM = ("EXP-030", 1800)


def prompt_by_id(pid: str) -> FinalPrompt:
    for p in FINAL_PROMPTS:
        if p.id == pid:
            return p
    raise KeyError(pid)


def build_prompt(style: str, template: str) -> str:
    spec = style_kit.style_by_key(style)
    return template.format(trigger=spec.trigger, phrase=STYLE_PHRASES[style])


def plan_for_arm(kind: str, geometry: str) -> list[tuple[str, int, float | None]]:
    """(prompt_id, seed, weight) triples for one arm in one process.

    Deduplicated. Blocks A and B overlap by construction - block A sweeps four
    weights over two prompts and two seeds, block B holds the weight at the
    nominal 0.7 across four prompts and three seeds - so (FP1/FP2, 42/1337, 0.7)
    falls in both. The first executed run generated those four cells twice per
    candidate arm, 24 redundant images in all, and they came back byte-identical.
    The duplicates are removed here rather than tolerated: they cost GPU time
    against a declared cap and they put a self-pair into every diversity cell they
    touched, biasing it toward zero.
    """
    plan: list[tuple[str, int, float | None]] = []
    if kind == "candidate" and geometry == "512x512":
        for pid in BLOCK_A_PROMPTS:                       # block A: weight sweep
            for seed in SEEDS_SWEEP:
                for weight in WEIGHTS_SWEEP:
                    plan.append((pid, seed, weight))
        for pid in BLOCK_B_PROMPTS:                       # block B: role + 3rd seed
            for seed in SEEDS_FULL:
                plan.append((pid, seed, WEIGHT_NOMINAL))
    elif kind == "candidate" and geometry == "512x1536":  # block C: deck format
        for seed in SEEDS_SWEEP:
            for weight in WEIGHTS_DECK:
                plan.append(("FP1-style", seed, weight))
    elif kind == "multi" and geometry == "512x512":       # blocks D + E
        for seed in SEEDS_SWEEP:
            for weight in WEIGHTS_SWEEP:
                plan.append(("FP1-style", seed, weight))
            plan.append(("FP2-shared", seed, 1.0))
    elif kind == "base" and geometry == "512x512":        # block F
        for pid in BLOCK_B_PROMPTS:
            for seed in SEEDS_SWEEP:
                plan.append((pid, seed, None))
    elif kind == "base" and geometry == "512x1536":
        for seed in SEEDS_SWEEP:
            plan.append(("FP1-style", seed, None))
    else:
        raise ValueError(f"no plan for kind={kind!r} geometry={geometry!r}")

    seen: set[tuple[str, int, float | None]] = set()
    unique: list[tuple[str, int, float | None]] = []
    for cell in plan:
        if cell not in seen:
            seen.add(cell)
            unique.append(cell)
    return unique


def planned_arms() -> list[dict]:
    """Every process this matrix will launch, in order. One arm = one process."""
    arms: list[dict] = []
    for exp_id, style, step in CANDIDATES:
        for geometry in ("512x512", "512x1536"):
            arms.append({"kind": "candidate", "arm": exp_id, "style": style,
                         "checkpoint_step": step, "geometry": geometry})
    for style in style_kit.STYLE_ORDER:
        arms.append({"kind": "multi", "arm": MULTI_STYLE_ARM[0], "style": style,
                     "checkpoint_step": MULTI_STYLE_ARM[1], "geometry": "512x512"})
    for style in style_kit.STYLE_ORDER:
        for geometry in ("512x512", "512x1536"):
            arms.append({"kind": "base", "arm": "BASE", "style": style,
                         "checkpoint_step": 0, "geometry": geometry})
    return arms


def planned_generations() -> int:
    return sum(len(plan_for_arm(a["kind"], a["geometry"])) for a in planned_arms())


def matrix_fingerprint() -> str:
    payload = json.dumps(
        {
            "prompts": [{"id": p.id, "role": p.role, "template": p.template} for p in FINAL_PROMPTS],
            "weights_sweep": list(WEIGHTS_SWEEP),
            "weights_deck": list(WEIGHTS_DECK),
            "weight_nominal": WEIGHT_NOMINAL,
            "seeds_sweep": list(SEEDS_SWEEP),
            "seeds_full": list(SEEDS_FULL),
            "candidates": [list(c) for c in CANDIDATES],
            "multi_style_arm": list(MULTI_STYLE_ARM),
            "planned_generations": planned_generations(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", required=True, choices=["candidate", "multi", "base"])
    parser.add_argument("--arm", required=True)
    parser.add_argument("--style", required=True, choices=list(style_kit.STYLE_ORDER))
    parser.add_argument("--checkpoint-dir", default="")
    parser.add_argument("--checkpoint-step", type=int, default=0)
    parser.add_argument("--geometry", required=True, choices=["512x512", "512x1536"])
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args(argv)

    plan = plan_for_arm(args.kind, args.geometry)
    width, height = (int(v) for v in args.geometry.split("x"))

    if args.plan_only:
        print(f"{args.arm} {args.style} {args.geometry}: {len(plan)} generations")
        return 0

    import psutil
    import torch
    from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline

    from ml.inference.benchmark import ResourceSampler

    is_base = args.kind == "base"
    if not is_base and not args.checkpoint_dir:
        print("a non-base arm needs --checkpoint-dir")
        return 2

    print(f"EXP-031 [{args.arm}] {args.style} ck{args.checkpoint_step} {args.geometry} "
          f"-> {len(plan)} images")

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    process = psutil.Process()
    sampler = ResourceSampler(torch, process)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    sampler.start()
    started = time.perf_counter()

    pipe = StableDiffusionPipeline.from_pretrained(
        BASE_MODEL_REPO_ID,
        revision=BASE_MODEL_REVISION,
        torch_dtype=torch.float16,
        safety_checker=None,
        requires_safety_checker=False,
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to("cuda")
    pipe.set_progress_bar_config(disable=True)

    adapter_sha = ""
    adapter_rel = ""
    if not is_base:
        ck_dir = Path(args.checkpoint_dir)
        if not ck_dir.is_absolute():
            ck_dir = REPO / ck_dir
        files = sorted(ck_dir.glob("*.safetensors"))
        if not files:
            print(f"no .safetensors in {ck_dir}")
            return 2
        adapter_sha = hashlib.sha256(files[0].read_bytes()).hexdigest()
        adapter_rel = str(files[0].relative_to(REPO)).replace("\\", "/")
        pipe.load_lora_weights(str(ck_dir), weight_name=files[0].name)
        print(f"  adapter {adapter_rel}  sha {adapter_sha[:16]}...")

    live_modules = sum(1 for _, m in pipe.unet.named_modules() if hasattr(m, "lora_A"))
    print(f"  live UNet LoRA modules: {live_modules}")

    rows = []
    for pid, seed, weight in plan:
        spec = prompt_by_id(pid)
        text = build_prompt(args.style, spec.template)
        generator = torch.Generator(device="cuda").manual_seed(seed)
        kwargs = {}
        if weight is not None:
            kwargs["cross_attention_kwargs"] = {"scale": weight}
        t0 = time.perf_counter()
        image = pipe(
            prompt=text,
            negative_prompt=prompt_kit.NEGATIVE_PROMPT,
            num_inference_steps=prompt_kit.STEPS,
            guidance_scale=prompt_kit.GUIDANCE_SCALE,
            width=width,
            height=height,
            generator=generator,
            **kwargs,
        ).images[0]
        seconds = round(time.perf_counter() - t0, 3)

        wtag = "base" if weight is None else f"w{weight:g}".replace(".", "p")
        name = (
            f"EXP-031__{args.arm}__{args.style}__ck{args.checkpoint_step:05d}"
            f"__{pid}__seed{seed}__{wtag}__{args.geometry}.png"
        )
        path = OUTPUT_ROOT / name
        image.save(path)
        rows.append(
            {
                "exp_id": "EXP-031",
                "kind": args.kind,
                "arm": args.arm,
                "style": args.style,
                "checkpoint_step": args.checkpoint_step,
                "adapter_path": adapter_rel,
                "adapter_sha256": adapter_sha,
                "live_lora_modules": live_modules,
                "prompt_id": pid,
                "prompt_role": spec.role,
                "prompt_text": text,
                "prompt_sha256": prompt_kit.text_sha256(text),
                "seed": seed,
                "lora_weight": weight,
                "width": width,
                "height": height,
                "steps": prompt_kit.STEPS,
                "guidance_scale": prompt_kit.GUIDANCE_SCALE,
                "scheduler": prompt_kit.SCHEDULER,
                "generate_seconds": seconds,
                "output_path": f"outputs/EXP-031/{name}",
                "output_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "matrix_fingerprint": matrix_fingerprint(),
                "timestamp_utc": utc_now(),
                "status": "ok",
            }
        )

    sampler.stop()
    wall = round(time.perf_counter() - started, 3)
    peak = round(torch.cuda.max_memory_allocated() / MIB, 2)
    for row in rows:
        row["peak_allocated_mb"] = peak
        row["peak_reserved_mb"] = round(torch.cuda.max_memory_reserved() / MIB, 2)
        row["peak_device_used_mb"] = round(sampler.peak_device_used_mb, 2)
        row["peak_process_rss_mb"] = round(sampler.peak_process_rss_mb, 2)
        row["arm_wall_seconds"] = wall

    with RESULTS.open("a", encoding="utf-8", newline="") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    print(f"  {len(rows)} images, peak {peak} MiB, {wall}s -> {RESULTS.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
