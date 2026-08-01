"""Phase-2 offline similarity indicators for Prototype 2 (EXP-014).

PHASE 2 ONLY. This module is never imported by `ml/inference/reference_conditioning.py`,
and a pytest parses that runner with `ast` to keep it that way. The reason is
structural, not stylistic: the CLIP image encoder used here is 2.35 GiB, and
loading it inside a text-only or img2img generation process purely to compute an
indicator would inflate exactly the VRAM figures the RQ6 method comparison rests
on - the same class of error as the EXP-005 allocator contamination.

So this runs AFTER all generation is finished, over the images on disk, in its own
process, on CPU by default. Its output goes to a SEPARATE file joined on
`output_sha256`; no similarity value is ever written into a generation row.

What each indicator is, and is not
----------------------------------

`dhash_distance_to_reference`
    Perceptual-hash Hamming distance. Model-free. A COARSE NEAR-COPY FLAG ONLY -
    not a measure of style, quality, or influence strength. At or below the
    project's existing threshold of 6 it flags an output for the copy-risk sheet.

`overall_reference_similarity`
    Cosine similarity of CLIP image embeddings, computed identically for every
    arm including the baseline. It entangles subject, composition, semantics,
    colour and style, so it is an OVERALL REFERENCE-IMAGE SIMILARITY indicator,
    never a "style similarity" score. Style transfer is judged by the human
    `style_consistency` rubric dimension; perceived reference control by the
    human `reference_influence`. This number informs; the rubric decides.

`similarity_to_baseline`
    The same metric against the output's own text-only baseline at the same
    condition and seed. Measures departure from baseline, not quality.

Stated limitation, not buried
-----------------------------
The CLIP tower used here is the same family IP-Adapter conditions on, so this
indicator is descriptive WITHIN a method and is not a neutral referee BETWEEN
methods. It is reported with that limitation attached everywhere it appears.

Run:
    .venv/Scripts/python.exe scripts/evaluate_similarity.py
"""

import time
from pathlib import Path

from ml.inference.reference_schema import (
    COPY_RISK_MAX_DHASH_DISTANCE,
    IP_ADAPTER_IMAGE_ENCODER_SUBFOLDER,
    IP_ADAPTER_REPO,
    IP_ADAPTER_REVISION,
    REFERENCES,
    STATUS_FAILED,
    STATUS_OK,
    SimilarityRow,
)

# The evaluation encoder is pinned exactly like a generation component, so an
# indicator can always be traced to the weights that produced it.
EVALUATION_ENCODER_REPO = IP_ADAPTER_REPO
EVALUATION_ENCODER_SUBFOLDER = IP_ADAPTER_IMAGE_ENCODER_SUBFOLDER
EVALUATION_ENCODER_REVISION = IP_ADAPTER_REVISION

TEXT_ONLY_METHOD = "text-only"


# --- pure joining logic (CPU, no model) --------------------------------------


def baseline_key(row: dict) -> tuple:
    """(prompt_id, seed, width, height) - what a text-only output depends on.

    Keyed on the PROMPT rather than the condition, deliberately. The text-only
    arm uses no reference at all, so its output is fully determined by prompt,
    seed and geometry; two conditions sharing a prompt share a baseline. That is
    what lets the stress conditions be compared against a baseline at all: C5
    uses `P2-geo` (as C2 does) and C6 uses `P1-poster` (as C1 does), so keying on
    the condition would have left every EXP-011 row with an empty
    `similarity_to_baseline` for no real reason.
    """
    return (row["prompt_id"], int(row["seed"]), int(row["width"]), int(row["height"]))


def baseline_index(generation_rows: list[dict]) -> dict[tuple, str]:
    """Map each baseline key to the text-only output hash that realises it."""
    index: dict[tuple, str] = {}
    for row in generation_rows:
        if row.get("method") != TEXT_ONLY_METHOD or row.get("status") != STATUS_OK:
            continue
        if not row.get("output_sha256"):
            continue
        index[baseline_key(row)] = row["output_sha256"]
    return index


def baseline_for(row: dict, index: dict[tuple, str]) -> str:
    """The baseline hash for a generation row, or "" when none was produced.

    An absent baseline yields an empty string and an empty similarity, never a
    substituted baseline from a different seed, prompt or geometry.
    """
    return index.get(baseline_key(row), "")


def is_copy_risk(distance: int | str, threshold: int = COPY_RISK_MAX_DHASH_DISTANCE) -> bool:
    """Near-copy candidates are flagged and KEPT, never deleted: an output that
    reproduces its reference is a first-class RQ11 finding."""
    try:
        return int(distance) <= threshold
    except (TypeError, ValueError):
        return False


def evaluable_rows(generation_rows: list[dict]) -> list[dict]:
    """Rows with an image on disk to evaluate. Failed and timed-out runs are
    excluded here but remain present in the generation results."""
    return [
        row
        for row in generation_rows
        if row.get("status") == STATUS_OK and row.get("output_path") and row.get("output_sha256")
    ]


# --- model-backed indicators -------------------------------------------------


def dhash_distance(path_a: Path, path_b: Path) -> int:
    from ml.dataset.hashing import dhash_file

    return int(dhash_file(path_a) - dhash_file(path_b))


class ClipImageEncoder:
    """CLIP ViT-H image embeddings at a pinned revision.

    CPU by default. If a GPU pass is ever needed, `device` is recorded on every
    row so that this evaluation workload can never be mistaken for part of a
    generation VRAM or latency figure.
    """

    def __init__(self, device: str = "cpu"):
        import torch
        from transformers import CLIPImageProcessor, CLIPVisionModelWithProjection

        self.device = device
        self.torch = torch
        started = time.perf_counter()
        self.model = CLIPVisionModelWithProjection.from_pretrained(
            EVALUATION_ENCODER_REPO,
            subfolder=EVALUATION_ENCODER_SUBFOLDER,
            revision=EVALUATION_ENCODER_REVISION,
            # float32 on CPU: half precision is not reliably supported there and
            # a silent dtype fallback would make these numbers unreproducible.
            torch_dtype=torch.float32 if device == "cpu" else torch.float16,
            use_safetensors=True,
        ).to(device)
        self.model.eval()

        # Built exactly the way diffusers builds it during generation, and for the
        # same reason. `models/image_encoder` in this repository contains only
        # `config.json` and `model.safetensors` - there is NO preprocessor_config.json -
        # so `CLIPImageProcessor.from_pretrained` on that subfolder has nothing to read.
        # diffusers 0.39.0 therefore constructs the processor from the encoder's own
        # image size (`loaders/ip_adapter.py`), and matching that keeps the Phase-2
        # embeddings preprocessed identically to the Phase-1 conditioning embeddings.
        image_size = self.model.config.image_size
        self.processor = CLIPImageProcessor(size=image_size, crop_size=image_size)
        self.image_size = image_size

        self.load_seconds = round(time.perf_counter() - started, 3)
        self._cache: dict[str, object] = {}

    def embed(self, path: Path):
        """L2-normalised image embedding, cached per path: every reference is
        embedded once rather than once per output that points at it."""
        key = str(path)
        if key in self._cache:
            return self._cache[key]

        from PIL import Image

        with Image.open(path) as img:
            image = img.convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            embedding = self.model(**inputs).image_embeds[0]
        embedding = embedding / embedding.norm()
        self._cache[key] = embedding
        return embedding

    def cosine(self, path_a: Path, path_b: Path) -> float:
        a, b = self.embed(path_a), self.embed(path_b)
        return round(float(self.torch.dot(a, b)), 6)


# --- the evaluation pass -----------------------------------------------------


def evaluate(
    generation_rows: list[dict],
    repo_root: Path,
    exp_id: str = "EXP-014",
    device: str = "cpu",
    progress=None,
) -> tuple[list[SimilarityRow], dict]:
    """Compute all Phase-2 indicators. Returns (rows, run_record).

    `run_record` carries the device, the pinned encoder, and the measured
    duration, so this workload is documented as its own labelled evaluation run
    and is excluded from every generation figure.
    """
    rows_to_evaluate = evaluable_rows(generation_rows)
    index = baseline_index(generation_rows)
    encoder = ClipImageEncoder(device=device)

    started = time.perf_counter()
    results: list[SimilarityRow] = []
    for position, row in enumerate(rows_to_evaluate, start=1):
        output_path = repo_root / row["output_path"]
        reference_id = row.get("reference_id", "")
        status, error_type, error_message = STATUS_OK, "", ""
        dhash_value: int | str = ""
        reference_similarity: float | str = ""
        baseline_similarity: float | str = ""

        baseline_sha = baseline_for(row, index)
        baseline_path = _path_for_hash(generation_rows, baseline_sha, repo_root)

        try:
            if not output_path.exists():
                raise FileNotFoundError(f"output missing at {row['output_path']}")

            # The text-only arm uses no reference, so it has no distance to one.
            # Its row is still written, because it is the baseline every other
            # row is measured against.
            if reference_id:
                reference_path = repo_root / REFERENCES[reference_id].repo_path
                dhash_value = dhash_distance(output_path, reference_path)
                reference_similarity = encoder.cosine(output_path, reference_path)

            if baseline_path is not None and baseline_path.exists():
                baseline_similarity = encoder.cosine(output_path, baseline_path)
        except Exception as err:  # noqa: BLE001
            status = STATUS_FAILED
            error_type = type(err).__name__
            error_message = (str(err).strip().splitlines() or [type(err).__name__])[0][:400]

        results.append(
            SimilarityRow(
                output_sha256=row["output_sha256"],
                exp_id=row.get("exp_id", ""),
                condition_id=row["condition_id"],
                method=row["method"],
                influence_level=row["influence_level"],
                strength_value=row.get("strength_value", ""),
                seed=int(row["seed"]),
                width=int(row["width"]),
                height=int(row["height"]),
                reference_id=reference_id,
                dhash_distance_to_reference=dhash_value,
                overall_reference_similarity=reference_similarity,
                similarity_to_baseline=baseline_similarity,
                baseline_output_sha256=baseline_sha,
                copy_risk_flag=is_copy_risk(dhash_value),
                evaluation_device=device,
                evaluation_encoder_repo_id=EVALUATION_ENCODER_REPO,
                evaluation_encoder_revision_sha=EVALUATION_ENCODER_REVISION,
                status=status,
                error_type=error_type,
                error_message=error_message,
            )
        )
        if progress and position % 25 == 0:
            progress(position, len(rows_to_evaluate))

    elapsed = round(time.perf_counter() - started, 3)
    run_record = {
        "exp_id": exp_id,
        "workload": "offline similarity evaluation (Phase 2) - NOT a generation measurement",
        "evaluation_device": device,
        "evaluation_encoder_repo_id": EVALUATION_ENCODER_REPO,
        "evaluation_encoder_subfolder": EVALUATION_ENCODER_SUBFOLDER,
        "evaluation_encoder_revision_sha": EVALUATION_ENCODER_REVISION,
        "evaluation_encoder_image_size": encoder.image_size,
        "evaluation_preprocessing": (
            f"CLIPImageProcessor(size={encoder.image_size}, crop_size={encoder.image_size}) - "
            "constructed the same way diffusers builds it during generation, because the "
            "image_encoder subfolder ships no preprocessor_config.json"
        ),
        "encoder_load_seconds": encoder.load_seconds,
        "evaluation_seconds": elapsed,
        "images_evaluated": len(results),
        "generation_rows_seen": len(generation_rows),
        "rows_skipped_not_ok": len(generation_rows) - len(rows_to_evaluate),
        "copy_risk_flagged": sum(1 for r in results if r.copy_risk_flag),
        "copy_risk_threshold_dhash": COPY_RISK_MAX_DHASH_DISTANCE,
        "limitation": (
            "The CLIP tower used here is the same family IP-Adapter conditions on, so "
            "overall_reference_similarity is descriptive WITHIN a method and is not a neutral "
            "referee BETWEEN methods. It is not a style score: style transfer is judged by the "
            "human style_consistency rubric dimension."
        ),
    }
    return results, run_record


def _path_for_hash(generation_rows: list[dict], output_sha: str, repo_root: Path) -> Path | None:
    if not output_sha:
        return None
    for row in generation_rows:
        if row.get("output_sha256") == output_sha and row.get("output_path"):
            return repo_root / row["output_path"]
    return None
