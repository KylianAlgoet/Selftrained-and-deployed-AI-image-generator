"""The frozen evaluation kit for every DeckForge AI model comparison.

Established in Prototype 1 (M3) as mandated by docs/05-experiment-methodology.md
and reused verbatim afterwards, so differences between runs are attributable to
the variable under test rather than to prompt drift.

Two properties make this trustworthy:

1. The three style prompts are built with `ml.dataset.captions.build_caption`,
   the same template that captions the training data. The kit is therefore
   coupled to the dataset by construction, and these prompts double as the
   pre-training baseline that Prototypes 3-4 measure LoRA effect against.
2. `kit_fingerprint()` hashes the whole kit and a pytest asserts it against a
   recorded constant. Any later edit - including an edit to the caption template
   underneath - fails loudly instead of silently invalidating comparisons.

Do not edit the constants below to "fix" a benchmark. Deviations belong in the
per-run record (see the benchmark result schema), never in the frozen kit.
"""

import hashlib
import json
from dataclasses import dataclass

from ml.dataset.captions import build_caption


@dataclass(frozen=True)
class PromptSpec:
    id: str
    text: str
    intent: str


PROMPTS: tuple[PromptSpec, ...] = (
    PromptSpec(
        id="P1-poster",
        text=build_caption("retro-poster", "a snarling wolf head in three flat colours with strong graphic shapes"),
        intent="retro-poster style fidelity; flat silkscreen colour fields as in the WPA source material",
    ),
    PromptSpec(
        id="P2-geo",
        text=build_caption(
            "minimal-geometric", "concentric triangles and circles in a restrained three-colour palette"
        ),
        intent="minimal-geometric style fidelity; hard edges and restrained palette",
    ),
    PromptSpec(
        id="P3-ukiyo",
        text=build_caption("ukiyo-e", "a great cresting wave beneath a pale moon"),
        intent="ukiyo-e style fidelity; line quality and flat colour separation",
    ),
    PromptSpec(
        id="P4-deck",
        text=build_caption("retro-poster", "a vertical totem of stacked skulls and lightning bolts"),
        intent="tall-format composition probe for the deck aspect ratio (RQ8)",
    ),
    PromptSpec(
        id="P5-control",
        # Deliberately NOT built from the caption template: this is the style-free
        # control that measures the untuned base-model prior.
        text="skateboard decal artwork, a flaming skull",
        intent="style-free control; baseline prior of the untuned base model",
    ),
)

# Frozen across every comparison. Models that ignore negative prompts (e.g.
# distilled models run at guidance 1.0) record that as a per-run deviation.
NEGATIVE_PROMPT = (
    "photograph, 3d render, text, watermark, signature, blurry, low quality, jpeg artifacts, frame, border"
)

# Candidate set named in docs/05-experiment-methodology.md, frozen here.
SEEDS: tuple[int, ...] = (42, 1337, 2026)

STEPS = 30
GUIDANCE_SCALE = 7.5
SCHEDULER = "DPMSolverMultistepScheduler"

# Track A: identical settings for every candidate - the controlled feasibility
# comparison (speed, VRAM, reliability). Track B resolutions are per-model and
# live in the benchmark configuration, since each model has its own native size.
TRACK_A_RESOLUTION: tuple[int, int] = (512, 512)


def prompt_by_id(prompt_id: str) -> PromptSpec:
    for prompt in PROMPTS:
        if prompt.id == prompt_id:
            return prompt
    raise KeyError(f"unknown prompt id {prompt_id!r}; expected one of {[p.id for p in PROMPTS]}")


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_kit() -> dict:
    """Order-stable, serialisable view of the kit - the input to the fingerprint."""
    return {
        "prompts": [{"id": p.id, "text": p.text} for p in PROMPTS],
        "negative_prompt": NEGATIVE_PROMPT,
        "seeds": list(SEEDS),
        "steps": STEPS,
        "guidance_scale": GUIDANCE_SCALE,
        "scheduler": SCHEDULER,
        "track_a_resolution": list(TRACK_A_RESOLUTION),
    }


def kit_fingerprint() -> str:
    payload = json.dumps(canonical_kit(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    print(json.dumps(canonical_kit(), indent=2))
    print(f"\nfingerprint: {kit_fingerprint()}")
