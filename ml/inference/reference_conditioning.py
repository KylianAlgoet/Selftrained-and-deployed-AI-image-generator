"""Prototype 2 Phase-1 reference-conditioning runner (RQ6, RQ7) - inference only.

PHASE 1 IS GENERATION MEASUREMENT ONLY. This module deliberately imports no
similarity or metric code, and a pytest asserts that it never will. Loading the
2.35 GiB CLIP image encoder into a text-only or img2img process purely to compute
an indicator would inflate exactly the VRAM figures the method comparison rests
on - the same class of error as the EXP-005 allocator contamination. Phase 2
(`ml/evaluation/similarity.py`) runs afterwards, in its own process, over the
finished images.

What each process loads:

  | process           | loads                                   | does NOT load             |
  |-------------------|-----------------------------------------|---------------------------|
  | text-only         | SD 1.5                                  | image encoder, adapter    |
  | img2img           | SD 1.5 (shared via `from_pipe`)         | image encoder, adapter    |
  | ip-adapter[-plus] | SD 1.5 + adapter + CLIP ViT-H encoder   | -                         |

The encoder inside an IP-Adapter process is a genuine, unavoidable cost of that
generation method and belongs in its VRAM figure. The same encoder used in Phase
2 for metrics is a different workload and enters no generation figure.

ONE PROCESS PER (method x resolution x memory tier). Influence levels share a
process, because tensor geometry does not change across levels; that sharing is
declared in `process_config_key` and checked by the clean-process spot check.

Pinning gap handled explicitly: diffusers 0.39.0 pops `revision` and forwards it
to the adapter weights but NOT to `CLIPVisionModelWithProjection.from_pretrained`
(loaders/ip_adapter.py:207), so the encoder would come from a moving `main`.
Since the encoder is 2.35 GiB of the download and shapes every embedding, this
runner loads it itself at the pinned revision and registers it before calling
`load_ip_adapter`, which then skips its own encoder load.

Run (one process, one method, one resolution):
    .venv/Scripts/python.exe -m ml.inference.reference_conditioning \
        --exp EXP-009 --method ip-adapter --width 512 --height 512 --levels sweep
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ml.evaluation import prompt_kit
from ml.inference.benchmark import (
    GENERATION_TIMEOUT_SECONDS,
    MIB,
    GenerationTimeout,
    ResourceSampler,
    load_pipeline,
    resolve_revision,
    sha256_bytes,
)
from ml.inference.bench_schema import MEMORY_TIERS, MODELS, next_tier
from ml.inference.reference_schema import (
    CONDITIONS,
    IP_ADAPTER_IMAGE_ENCODER_SUBFOLDER,
    IP_ADAPTER_REVISION,
    LEVEL_VALUES,
    METHODS,
    REFERENCES,
    STATUS_FAILED,
    STATUS_OK,
    STATUS_TIMEOUT,
    SWEEP_VALUES,
    MethodSpec,
    ReferenceResultRow,
    ReferenceSpec,
    append_jsonl,
    build_output_filename,
    effective_steps,
    level_for_value,
    process_config_key,
    read_jsonl,
    render_summary_markdown,
    retained_area_fraction,
    summarize,
    write_csv,
)

def _first_line(err: BaseException, limit: int = 400) -> str:
    """First line of an exception message, never empty.

    Some CUDA and safetensors errors carry an empty `str()`; taking
    `str(err).splitlines()[0]` directly would then raise IndexError inside the
    handler and destroy the very failure this project is required to record.
    """
    text = str(err).strip()
    if not text:
        return f"({type(err).__name__} raised with no message)"
    return text.splitlines()[0][:limit]


REPO = Path(__file__).resolve().parents[2]
OUTPUTS = REPO / "outputs"
EVIDENCE = REPO / "docs" / "evidence"

SD15 = MODELS["sd15"]

# The reference is bounded before it reaches the CLIP processor, so a 4000 px
# scan does not cost a needless full-size decode-and-resize on every run. The
# processor's own 224 px centre-crop is unaffected by this bound.
MAX_REFERENCE_LONG_SIDE = 1024


# --- reference preprocessing -------------------------------------------------


def load_reference(spec: ReferenceSpec):
    from PIL import Image

    path = REPO / spec.repo_path
    if not path.exists():
        raise FileNotFoundError(
            f"reference {spec.id} missing at {spec.repo_path}; run scripts/build_reference_kit.py"
        )
    with Image.open(path) as img:
        return img.convert("RGB")


def preprocess_for_adapter(image):
    """IP-Adapter path: output geometry is untouched. The pipeline's own
    CLIPImageProcessor resizes and centre-crops to 224 regardless of the
    reference's native size, so nothing here is aspect-destructive."""
    from PIL import Image

    longest = max(image.size)
    if longest <= MAX_REFERENCE_LONG_SIDE:
        return image, f"native size {image.width}x{image.height}; CLIP processor resize + centre-crop 224"
    scale = MAX_REFERENCE_LONG_SIDE / longest
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    return resized, (
        f"long side bounded {image.width}x{image.height} -> {resized.width}x{resized.height} (LANCZOS); "
        "CLIP processor resize + centre-crop 224"
    )


def preprocess_for_img2img(image, width: int, height: int):
    """img2img path: the reference MUST become exactly (width, height), so it is
    centre-cropped to the target aspect and then resized. The discarded fraction
    is recorded per run as `reference_retained_area_fraction`."""
    from PIL import Image

    target_aspect = width / height
    source_aspect = image.width / image.height
    if source_aspect > target_aspect:
        crop_width = round(image.height * target_aspect)
        left = (image.width - crop_width) // 2
        box = (left, 0, left + crop_width, image.height)
    else:
        crop_height = round(image.width / target_aspect)
        top = (image.height - crop_height) // 2
        box = (0, top, image.width, top + crop_height)
    cropped = image.crop(box)
    resized = cropped.resize((width, height), Image.LANCZOS)
    return resized, (
        f"centre-crop {image.width}x{image.height} -> {cropped.width}x{cropped.height} "
        f"then LANCZOS resize to {width}x{height}"
    )


# --- pipeline construction ---------------------------------------------------


def attach_ip_adapter(pipe, method: MethodSpec, dtype_name: str) -> str:
    """Register a PINNED image encoder, then load the adapter. Returns the
    encoder revision actually used.

    Order matters: `load_ip_adapter` only loads an encoder when none is already
    registered, and it would load that one from a moving `main`.
    """
    import torch
    from transformers import CLIPVisionModelWithProjection

    dtype = getattr(torch, dtype_name)
    encoder = CLIPVisionModelWithProjection.from_pretrained(
        method.repo_id,
        subfolder=IP_ADAPTER_IMAGE_ENCODER_SUBFOLDER,
        revision=IP_ADAPTER_REVISION,
        torch_dtype=dtype,
        use_safetensors=True,
    ).to(pipe.device)
    pipe.register_modules(image_encoder=encoder)

    pipe.load_ip_adapter(
        method.repo_id,
        subfolder=method.subfolder,
        weight_name=method.weight_name,
        revision=IP_ADAPTER_REVISION,
    )
    return IP_ADAPTER_REVISION


def adapter_attention_processors(pipe) -> list[str]:
    """Names of the UNet attention processors that are IP-Adapter processors.

    Verified from the live module rather than assumed from a successful call:
    `load_ip_adapter` replacing nothing would still return without error.
    """
    return sorted(
        {
            type(processor).__name__
            for processor in pipe.unet.attn_processors.values()
            if "IPAdapter" in type(processor).__name__
        }
    )


def build_pipelines(method: MethodSpec, revision: str, tier: int, dtype_name: str) -> tuple:
    """Returns (generation_pipe, adapter_pipe, load_seconds, safety_present,
    safety_enabled, vae_variant, encoder_revision, adapter_processors).

    `adapter_pipe` is the object `set_ip_adapter_scale` is called on; for the two
    SD 1.5-native arms it is None.

    SD 1.5 is loaded through Prototype 1's own `load_pipeline`, unchanged, so the
    scheduler, dtype, safety-checker policy and memory tiers are identical to the
    baselines these results are compared against.
    """
    start = time.perf_counter()
    pipe, base_load_seconds, safety_present, safety_enabled, vae_variant = load_pipeline(
        SD15, revision, tier, dtype_name
    )

    encoder_revision = ""
    adapter_processors: list[str] = []
    generation_pipe = pipe

    if method.key == "img2img":
        from diffusers import AutoPipelineForImage2Image

        # Derives the img2img pipeline from the ALREADY-LOADED components: no
        # reload, no extra memory, and provably identical weights to the
        # text-only arm.
        generation_pipe = AutoPipelineForImage2Image.from_pipe(pipe)
        generation_pipe.set_progress_bar_config(disable=True)
    elif method.loads_image_encoder:
        encoder_revision = attach_ip_adapter(pipe, method, dtype_name)
        adapter_processors = adapter_attention_processors(pipe)
        if not adapter_processors:
            raise RuntimeError(
                f"{method.key}: load_ip_adapter returned without installing any IP-Adapter "
                "attention processor in the UNet"
            )

    load_seconds = round(time.perf_counter() - start, 3)
    del base_load_seconds
    return (
        generation_pipe,
        pipe if method.loads_image_encoder else None,
        load_seconds,
        safety_present,
        safety_enabled,
        vae_variant,
        encoder_revision,
        adapter_processors,
    )


# --- a single measured run ---------------------------------------------------


def generate_once(
    pipe,
    torch,
    method: MethodSpec,
    prompt_text: str,
    seed: int,
    width: int,
    height: int,
    reference_image,
    strength_value: float | None,
) -> tuple:
    """Returns (image, generate_seconds). Timing is synchronised on both sides;
    CUDA is asynchronous, so unsynchronised timing would be fiction."""
    generator = torch.Generator(device="cuda").manual_seed(seed)
    deadline = time.perf_counter() + GENERATION_TIMEOUT_SECONDS

    def on_step_end(pipeline, step, timestep, callback_kwargs):
        if time.perf_counter() > deadline:
            raise GenerationTimeout(
                f"generation exceeded {GENERATION_TIMEOUT_SECONDS:.0f}s budget at step {step}"
            )
        return callback_kwargs

    kwargs = dict(
        prompt=prompt_text,
        negative_prompt=prompt_kit.NEGATIVE_PROMPT,
        num_inference_steps=prompt_kit.STEPS,
        guidance_scale=prompt_kit.GUIDANCE_SCALE,
        generator=generator,
        callback_on_step_end=on_step_end,
    )

    if method.key == "img2img":
        # img2img takes no width/height: the output geometry is the init image's,
        # which preprocess_for_img2img has already forced to exactly (W, H).
        kwargs["image"] = reference_image
        kwargs["strength"] = strength_value
    else:
        kwargs["width"] = width
        kwargs["height"] = height
        if method.loads_image_encoder:
            kwargs["ip_adapter_image"] = reference_image

    torch.cuda.synchronize()
    start = time.perf_counter()
    result = pipe(**kwargs)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    return result.images[0], round(elapsed, 3)


# --- the run plan ------------------------------------------------------------


def resolve_levels(method_key: str, spec: str) -> list[tuple[str, float | None]]:
    """`spec` is a comma-separated list of shared level names, in which the token
    `sweep` expands to that method's full sweep values.

    Returns (influence_level, native_value) pairs, de-duplicated on the native
    value and in the order requested. For sweep points the level label is derived
    through the SAME table the named levels use, so a chart can never be read
    against the wrong direction.

    Mixing the two matters for the clean-process spot check. The sweep values and
    the named levels are deliberately different numbers (img2img sweeps
    0.90...0.30 but its named levels are 0.85/0.65/0.40), so a spot check run at
    the named levels would have NO shared-process counterpart to be compared
    against. `--levels sweep,weak,medium,strong` puts both in the one shared
    process, which is exactly what EXP-008b and EXP-009b then re-run cleanly.
    """
    # The text-only control has no reference-strength parameter at all, so it has
    # exactly one level whatever is requested - including 'sweep', which would
    # otherwise fail on a method that owns no sweep values.
    if method_key == "text-only":
        return [("none", None)]

    table = LEVEL_VALUES[method_key]
    pairs: list[tuple[str, float | None]] = []
    seen: set[float] = set()

    for name in [part.strip() for part in spec.split(",") if part.strip()]:
        if name == "sweep":
            candidates = [
                (level_for_value(method_key, value), value) for value in SWEEP_VALUES[method_key]
            ]
        elif name in table:
            candidates = [(name, table[name])]
        else:
            raise SystemExit(
                f"method {method_key!r} has no {name!r} level; available: {sorted(table)} or 'sweep'"
            )
        for level, value in candidates:
            if value in seen:
                continue
            seen.add(value)
            pairs.append((level, value))

    if not pairs:
        raise SystemExit(f"no levels resolved from {spec!r} for method {method_key!r}")
    return pairs


def run_process(
    exp_id: str,
    method: MethodSpec,
    condition_ids: list[str],
    levels: list[tuple[str, float | None]],
    seeds: tuple[int, ...],
    width: int,
    height: int,
    dtype_name: str,
    revision: str,
    jsonl_path: Path,
    warmup: bool,
    diagnostics: dict | None = None,
) -> list[ReferenceResultRow]:
    """One (method, resolution, tier) combination, in this process only.

    A deeper memory tier is entered ONLY after the failure that justified it has
    been written as its own row, and a tier change is recorded in
    `process_config_key` so the boundary stays auditable.

    `diagnostics`, when supplied, receives the UNet attention-processor evidence
    and the final tier, so the EXP-007 gate can record that the adapter was
    genuinely attached rather than merely that `load_ip_adapter` returned.
    """
    import psutil
    import torch
    from diffusers import __version__ as diffusers_version

    process = psutil.Process()
    gpu_name = torch.cuda.get_device_name(0)
    out_dir = OUTPUTS / exp_id
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[ReferenceResultRow] = []
    tier = 0
    pipe = None
    adapter_pipe = None
    load_seconds: float | str = "not measured"
    safety_present = safety_enabled = False
    vae_variant = "pipeline default"
    encoder_revision = ""
    adapter_processors: list[str] = []

    def base_row(**overrides) -> ReferenceResultRow:
        defaults = dict(
            exp_id=exp_id,
            condition_id="",
            method=method.key,
            timestamp_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            model_repo_id=SD15.repo_id,
            model_revision_sha=revision,
            method_repo_id=method.repo_id,
            method_revision_sha=IP_ADAPTER_REVISION if method.repo_id else "",
            image_encoder_revision_sha=encoder_revision,
            torch_version=torch.__version__,
            torch_cuda_version=str(torch.version.cuda),
            diffusers_version=diffusers_version,
            gpu_name=gpu_name,
            dtype=dtype_name,
            scheduler=prompt_kit.SCHEDULER,
            prompt_id="",
            prompt_sha256="",
            negative_prompt_sha256=prompt_kit.text_sha256(prompt_kit.NEGATIVE_PROMPT),
            reference_id="",
            reference_sha256="",
            reference_preprocess="",
            reference_retained_area_fraction="",
            influence_level="",
            strength_param_name=method.strength_param_name,
            strength_value="",
            effective_steps="",
            seed=0,
            width=width,
            height=height,
            steps=prompt_kit.STEPS,
            guidance_scale=prompt_kit.GUIDANCE_SCALE,
            memory_tier=tier,
            process_config_key=process_config_key(method.key, width, height, tier),
            safety_checker_present=safety_present,
            safety_checker_enabled=safety_enabled,
            vae_variant=vae_variant,
            load_seconds=load_seconds,
            generate_seconds="not measured",
            peak_vram_allocated_mb="not measured",
            peak_vram_reserved_mb="not measured",
            peak_device_used_mb="not measured",
            peak_process_rss_mb="not measured",
            output_sha256="",
            status=STATUS_OK,
        )
        defaults.update(overrides)
        return ReferenceResultRow(**defaults)

    while pipe is None:
        try:
            print(f"  loading {method.label} at tier {tier} ({MEMORY_TIERS[tier]})")
            (
                pipe,
                adapter_pipe,
                load_seconds,
                safety_present,
                safety_enabled,
                vae_variant,
                encoder_revision,
                adapter_processors,
            ) = build_pipelines(method, revision, tier, dtype_name)
        except Exception as err:  # noqa: BLE001
            row = base_row(
                status=STATUS_FAILED,
                error_type=type(err).__name__,
                error_message=_first_line(err),
                prompt_id="(load)",
            )
            rows.append(row)
            append_jsonl(row, jsonl_path)
            print(f"  LOAD FAILED at tier {tier}: {type(err).__name__}: {_first_line(err, 200)}")
            escalated = next_tier(tier)
            if escalated is None:
                print("  no comparable memory tier remains - method declared infeasible here")
                return rows
            tier = escalated
            continue

    if diagnostics is not None:
        diagnostics["adapter_attention_processors"] = adapter_processors
        diagnostics["adapter_attention_processor_count"] = sum(
            1 for p in pipe.unet.attn_processors.values() if "IPAdapter" in type(p).__name__
        )
        diagnostics["unet_attention_processor_count"] = len(pipe.unet.attn_processors)
        diagnostics["image_encoder_revision_sha"] = encoder_revision
        diagnostics["memory_tier"] = tier
        diagnostics["post_load_vram_allocated_mb"] = round(torch.cuda.memory_allocated() / MIB, 2)
        diagnostics["post_load_vram_reserved_mb"] = round(torch.cuda.memory_reserved() / MIB, 2)

    if adapter_processors:
        print(f"  IP-Adapter attention processors present: {adapter_processors}")
        print(f"  image encoder pinned at {encoder_revision}")

    # References are decoded once per process rather than per run: decode time is
    # not part of the method's cost and would otherwise pollute every timing.
    references: dict[str, tuple] = {}
    for condition_id in condition_ids:
        reference_id = CONDITIONS[condition_id].reference_id
        if reference_id in references:
            continue
        spec = REFERENCES[reference_id]
        image = load_reference(spec)
        if method.key == "img2img":
            prepared, note = preprocess_for_img2img(image, width, height)
            retained = round(retained_area_fraction(spec.width, spec.height, width, height), 4)
        elif method.loads_image_encoder:
            prepared, note = preprocess_for_adapter(image)
            # IP-Adapter does not crop to the output geometry, so nothing of the
            # reference is discarded on account of the deck aspect.
            retained = 1.0
        else:
            prepared, note, retained = None, "not applicable - no reference used", ""
        references[reference_id] = (prepared, note, retained, spec)

    if warmup:
        # Discarded: the first generation includes kernel autotuning and would
        # inflate the measurement. One warm-up per (process, resolution).
        print(f"  warm-up at {width}x{height} (discarded)")
        try:
            first_condition = CONDITIONS[condition_ids[0]]
            prepared = references[first_condition.reference_id][0]
            _, value = levels[0]
            generate_once(
                pipe,
                torch,
                method,
                prompt_kit.prompt_by_id(first_condition.prompt_id).text,
                prompt_kit.SEEDS[0],
                width,
                height,
                prepared,
                value,
            )
        except Exception as err:  # noqa: BLE001
            print(f"  warm-up failed ({type(err).__name__}) - continuing to measured runs")

    for level, value in levels:
        if method.loads_image_encoder:
            adapter_pipe.set_ip_adapter_scale(value)
        for condition_id in condition_ids:
            condition = CONDITIONS[condition_id]
            prompt = prompt_kit.prompt_by_id(condition.prompt_id)
            prepared, note, retained, spec = references[condition.reference_id]

            for seed in seeds:
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.synchronize()
                sampler = ResourceSampler(torch, process)
                sampler.start()
                status, error_type, error_message = STATUS_OK, "", ""
                generate_seconds: float | str = "not measured"
                output_sha, output_path = "", ""

                try:
                    image, generate_seconds = generate_once(
                        pipe, torch, method, prompt.text, seed, width, height, prepared, value
                    )
                    filename = build_output_filename(
                        exp_id, method.slug, condition_id, condition.reference_id, level,
                        value, width, height, seed, tier,
                    )
                    destination = out_dir / filename
                    image.save(destination)
                    output_sha = sha256_bytes(destination)
                    output_path = str(destination.relative_to(REPO)).replace("\\", "/")
                except GenerationTimeout as err:
                    status, error_type, error_message = STATUS_TIMEOUT, type(err).__name__, _first_line(err)
                except Exception as err:  # noqa: BLE001
                    status, error_type, error_message = (
                        STATUS_FAILED, type(err).__name__, _first_line(err),
                    )
                finally:
                    sampler.stop()

                row = base_row(
                    condition_id=condition_id,
                    prompt_id=prompt.id,
                    prompt_sha256=prompt_kit.text_sha256(prompt.text),
                    reference_id=condition.reference_id if method.key != "text-only" else "",
                    reference_sha256=(
                        "" if method.key == "text-only" else _reference_sha(spec)
                    ),
                    reference_preprocess=note,
                    reference_retained_area_fraction=retained,
                    influence_level=level,
                    strength_value="" if value is None else value,
                    effective_steps=effective_steps(method.key, prompt_kit.STEPS, value),
                    seed=seed,
                    memory_tier=tier,
                    process_config_key=process_config_key(method.key, width, height, tier),
                    safety_checker_present=safety_present,
                    safety_checker_enabled=safety_enabled,
                    vae_variant=vae_variant,
                    load_seconds=load_seconds,
                    generate_seconds=generate_seconds,
                    peak_vram_allocated_mb=round(torch.cuda.max_memory_allocated() / MIB, 2),
                    peak_vram_reserved_mb=round(torch.cuda.max_memory_reserved() / MIB, 2),
                    peak_device_used_mb=round(sampler.peak_device_used_mb, 2),
                    peak_process_rss_mb=round(sampler.peak_process_rss_mb, 2),
                    output_sha256=output_sha,
                    status=status,
                    error_type=error_type,
                    error_message=error_message,
                    output_path=output_path,
                )
                rows.append(row)
                append_jsonl(row, jsonl_path)
                marker = "ok" if status == STATUS_OK else status.upper()
                print(
                    f"  [{marker}] {method.key} {condition_id} {level}"
                    f"({method.strength_param_name}={value}) seed={seed} {width}x{height} "
                    f"{generate_seconds}s alloc={row.peak_vram_allocated_mb}MiB"
                    + (f" :: {error_type}: {error_message[:120]}" if error_type else "")
                )

    del pipe
    torch.cuda.empty_cache()
    return rows


_SHA_CACHE: dict[str, str] = {}


def _reference_sha(spec: ReferenceSpec) -> str:
    if spec.id not in _SHA_CACHE:
        from ml.dataset.hashing import sha256_file

        _SHA_CACHE[spec.id] = sha256_file(REPO / spec.repo_path)
    return _SHA_CACHE[spec.id]


# --- entry point -------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prototype 2 reference-conditioning runner (one method, one resolution, one process)"
    )
    parser.add_argument("--exp", required=True, help="experiment id, e.g. EXP-009")
    parser.add_argument("--method", required=True, choices=sorted(METHODS))
    parser.add_argument("--conditions", default=",".join(("C1", "C2", "C3", "C4")))
    parser.add_argument("--levels", default="sweep", help="'sweep' or comma-separated level names")
    parser.add_argument("--seeds", default="", help="comma-separated; defaults to the frozen kit seeds")
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--dtype", default="float16", choices=["float16", "bfloat16", "float32"])
    parser.add_argument("--no-warmup", action="store_true")
    parser.add_argument("--suffix", default="", help="distinguishes result files within one experiment")
    parser.add_argument(
        "--gate",
        action="store_true",
        help="EXP-007 mode: also write an adapter-gate JSON recording the attached attention "
        "processors, both pinned revisions, and post-load VRAM",
    )
    args = parser.parse_args(argv)

    import torch

    if not torch.cuda.is_available():
        print("CUDA is not available - refusing to run. Fix the EXP-001 gate first.", file=sys.stderr)
        return 2

    method = METHODS[args.method]
    condition_ids = [c.strip() for c in args.conditions.split(",") if c.strip()]
    unknown = [c for c in condition_ids if c not in CONDITIONS]
    if unknown:
        print(f"unknown conditions: {unknown}; known: {sorted(CONDITIONS)}", file=sys.stderr)
        return 2

    seeds = (
        tuple(int(s) for s in args.seeds.split(",") if s.strip())
        if args.seeds
        else prompt_kit.SEEDS
    )
    levels = resolve_levels(method.key, args.levels)

    evidence_dir = EVIDENCE / args.exp
    evidence_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"-{args.suffix}" if args.suffix else ""
    stem = f"{method.slug}-{args.width}x{args.height}{suffix}"
    jsonl_path = evidence_dir / f"results-{stem}.jsonl"
    if jsonl_path.exists():
        jsonl_path.unlink()  # a re-run replaces its own results rather than appending twice

    revision = resolve_revision(SD15.repo_id)
    print(f"\n=== {args.exp} :: {method.label} @ {args.width}x{args.height} ===")
    print(f"SD 1.5 pinned revision: {revision}")
    if method.repo_id:
        print(f"adapter: {method.repo_id}/{method.subfolder}/{method.weight_name} @ {IP_ADAPTER_REVISION}")
    print(f"kit fingerprint: {prompt_kit.kit_fingerprint()}")
    print(f"process: {process_config_key(method.key, args.width, args.height, 0)}")
    print(f"levels: {levels}")
    print(f"conditions: {condition_ids} x seeds {seeds}")

    diagnostics: dict = {}
    rows = run_process(
        args.exp, method, condition_ids, levels, seeds, args.width, args.height,
        args.dtype, revision, jsonl_path, warmup=not args.no_warmup,
        diagnostics=diagnostics,
    )
    print(f"{len(rows)} rows recorded in this process")

    if not jsonl_path.exists():
        print("no rows written", file=sys.stderr)
        return 1

    disk_rows = read_jsonl(jsonl_path)
    write_csv(disk_rows, evidence_dir / f"results-{stem}.csv")
    summaries = summarize(disk_rows)
    (evidence_dir / f"summary-{stem}.md").write_text(
        render_summary_markdown(summaries, f"{args.exp} measurements - {method.label} @ {args.width}x{args.height}"),
        encoding="utf-8",
    )

    if args.gate:
        ok_rows = [r for r in disk_rows if r["status"] == STATUS_OK]
        gate = {
            "experiment": args.exp,
            "method": method.key,
            "adapter_repo_id": method.repo_id,
            "adapter_weight_name": method.weight_name,
            "adapter_revision_sha": IP_ADAPTER_REVISION if method.repo_id else "",
            "image_encoder_subfolder": IP_ADAPTER_IMAGE_ENCODER_SUBFOLDER if method.loads_image_encoder else "",
            "image_encoder_revision_sha": ok_rows[0]["image_encoder_revision_sha"] if ok_rows else "",
            # Read back from the live UNet, not inferred from a successful call:
            # `load_ip_adapter` replacing nothing would still return without error.
            "adapter_attention_processors": diagnostics.get("adapter_attention_processors", []),
            "adapter_attention_processor_count": diagnostics.get(
                "adapter_attention_processor_count", "not measured"
            ),
            "unet_attention_processor_count": diagnostics.get(
                "unet_attention_processor_count", "not measured"
            ),
            "post_load_vram_allocated_mb": diagnostics.get("post_load_vram_allocated_mb", "not measured"),
            "post_load_vram_reserved_mb": diagnostics.get("post_load_vram_reserved_mb", "not measured"),
            "sd15_repo_id": SD15.repo_id,
            "sd15_revision_sha": revision,
            "kit_fingerprint": prompt_kit.kit_fingerprint(),
            "runs_ok": len(ok_rows),
            "runs_total": len(disk_rows),
            "peak_vram_allocated_mb": ok_rows[0]["peak_vram_allocated_mb"] if ok_rows else "not measured",
            "peak_vram_reserved_mb": ok_rows[0]["peak_vram_reserved_mb"] if ok_rows else "not measured",
            "peak_device_used_mb": ok_rows[0]["peak_device_used_mb"] if ok_rows else "not measured",
            "load_seconds": ok_rows[0]["load_seconds"] if ok_rows else "not measured",
            "generate_seconds": ok_rows[0]["generate_seconds"] if ok_rows else "not measured",
            "process_config_key": process_config_key(method.key, args.width, args.height, 0),
        }
        (evidence_dir / f"gate-{stem}.json").write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
        print(f"gate evidence: {evidence_dir / f'gate-{stem}.json'}")

    ok = sum(1 for r in disk_rows if r["status"] == STATUS_OK)
    print(f"\n{ok}/{len(disk_rows)} runs ok. Results: {jsonl_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
