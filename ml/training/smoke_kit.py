"""The frozen Prototype 3 (M5) LoRA smoke-test kit.

Everything a smoke-test run is allowed to vary is fixed here BEFORE any GPU work,
so no run can quietly reselect its own data, captions, prompts, seeds or adapter
weights and then be compared against a differently-configured sibling.

Deliberately free of torch/diffusers/PIL imports, exactly like
`ml.inference.bench_schema` and `ml.inference.reference_schema`, so the whole kit
is unit-testable on any machine without a GPU.

Four things are frozen:

1. **The training subset** - an explicit tuple of dataset-v1 item IDs, plus the
   deterministic rule that produced it. `data/manifests/smoke-test-p3.csv` is the
   committed, hash-verified expansion. No run samples a new random subset.
2. **The caption strategy** - dataset-v1 captions are used VERBATIM, with no
   trigger token. See CAPTION_STRATEGY below for why.
3. **The validation prompts and seeds** - drawn from the frozen evaluation kit
   (`ml.evaluation.prompt_kit`, fingerprint c40749bc...) so Prototype 3 results
   stay comparable with the Prototype 1 and 2 baselines.
4. **The adapter weights under test** - 0.0 (lower-bound diagnostic) and 1.0
   (changed-output test).

`kit_fingerprint()` hashes the whole thing and a pytest asserts it against a
recorded constant, the same protection `prompt_kit` carries. Do not edit these
constants to make a run pass; deviations belong in the per-run record.
"""

import hashlib
import json
from dataclasses import dataclass

# --- The frozen training subset ----------------------------------------------

DATASET_VERSION = "dataset-v1"
SMOKE_MANIFEST_PATH = "data/manifests/smoke-test-p3.csv"

# Style chosen deliberately over `retro-poster` and `ukiyo-e`:
#
#   * it is project-original generated artwork (ml/dataset/generate_geometric.py),
#     so it carries no licence question at all, and
#   * EXP-011 confirmed that framed, text-dominated source material transfers
#     unwanted frames and pseudo-text into outputs for BOTH conditioning methods
#     at medium influence and above. `retro-poster` is exactly that material.
#     A feasibility smoke test should not also be fighting a known dataset
#     contamination.
SMOKE_STYLE = "minimal-geometric"

# The deterministic selection rule, recorded so the subset is reproducible from
# the repository alone rather than from this file's contents being trusted:
#
#   filter dataset-v1 to style == SMOKE_STYLE and split == "train"
#   sort by `id` ascending
#   take the first SMOKE_SUBSET_SIZE
#
# No RNG is involved. The pool is 44 items; the first 12 by ID happen to cover
# all 6 palette indices and all 6 shape counts used by the generator, so the
# simplest auditable rule is also well spread. That coverage is asserted by a
# pytest, so it cannot silently degrade if the manifest is ever rebuilt.
SMOKE_SUBSET_SIZE = 12
SMOKE_SELECTION_RULE = (
    "style == 'minimal-geometric' and split == 'train', sorted by id ascending, first 12"
)

# The expansion of the rule above, frozen. A pytest re-derives this from
# dataset-v1 and fails if the two disagree, which catches both an edit here and
# an upstream change to dataset-v1.
SMOKE_ITEM_IDS: tuple[str, ...] = (
    "DS-0001",
    "DS-0002",
    "DS-0003",
    "DS-0004",
    "DS-0005",
    "DS-0006",
    "DS-0007",
    "DS-0008",
    "DS-0009",
    "DS-0010",
    "DS-0011",
    "DS-0012",
)

# Every smoke item must be a training item. The holdout and validation splits are
# never touched by Prototype 3; a pytest enforces this against dataset-v1 rather
# than trusting the manifest's own `split` column.
FORBIDDEN_SPLITS: tuple[str, ...] = ("val", "holdout")

# --- The frozen caption strategy ---------------------------------------------

# Dataset-v1 captions are used VERBATIM. No trigger token, no rewriting, no
# per-run caption synthesis.
#
# Why no trigger token: `ml/dataset/captions.py` states that "Final trigger-token
# design for LoRA training is decided in Prototypes 3-4". M5 is a *feasibility*
# test - does a LoRA train, save, reload and measurably change generation, and
# what does it cost. Introducing a trigger token here would add a second variable
# to a run whose only question is technical, and would make the M5 captions
# non-comparable with the frozen evaluation prompts that Prototype 1 and 2 used.
# Trigger-token design therefore remains an open Prototype 4 (M6) decision.
CAPTION_STRATEGY = "dataset-v1 captions verbatim; no trigger token (trigger-token design deferred to Prototype 4)"

# The style phrase every smoke caption begins with, from
# `ml.dataset.captions.STYLE_PHRASES["minimal-geometric"]`. Recorded here so a
# rename upstream fails a test instead of silently changing what was trained.
SMOKE_STYLE_PHRASE = "minimal geometric abstract style"

# --- The frozen validation kit -----------------------------------------------


@dataclass(frozen=True)
class ValidationCase:
    id: str
    prompt_id: str
    intent: str


# Both prompts come from the frozen evaluation kit (fingerprint c40749bc...), so
# the Prototype 3 validation images are directly comparable with the Prototype 1
# and Prototype 2 baselines generated from the same prompts.
VALIDATION_CASES: tuple[ValidationCase, ...] = (
    ValidationCase(
        id="V1-target-style",
        prompt_id="P2-geo",
        intent=(
            "the trained style: if the adapter changed anything, it should be most "
            "visible on the prompt whose style the LoRA was trained on"
        ),
    ),
    ValidationCase(
        id="V2-control",
        prompt_id="P5-control",
        intent=(
            "style-free control: measures whether the adapter perturbs generation even "
            "where no style was requested, which separates a real style effect from a "
            "global shift"
        ),
    ),
)

# A subset of the frozen kit's (42, 1337, 2026). Seed 42 is the seed every
# earlier milestone reported single-image comparisons at.
VALIDATION_SEEDS: tuple[int, ...] = (42, 1337)

# The two adapter weights under test.
#   0.0 - lower-bound DIAGNOSTIC. Byte equality with the text-only baseline is a
#         strong positive result but is NOT a pass condition: loading an inactive
#         adapter may legitimately change the execution graph or numerical path.
#   1.0 - changed-output test. A differing PNG hash alone is NOT sufficient
#         evidence of a real change; see docs for the full indicator set.
LORA_WEIGHT_LOWER_BOUND = 0.0
LORA_WEIGHT_ACTIVE = 1.0
VALIDATION_LORA_WEIGHTS: tuple[float, ...] = (LORA_WEIGHT_LOWER_BOUND, LORA_WEIGHT_ACTIVE)

# --- Fingerprint --------------------------------------------------------------


def canonical_kit() -> dict:
    """Order-stable, serialisable view of the kit - the input to the fingerprint."""
    return {
        "dataset_version": DATASET_VERSION,
        "smoke_manifest_path": SMOKE_MANIFEST_PATH,
        "smoke_style": SMOKE_STYLE,
        "smoke_subset_size": SMOKE_SUBSET_SIZE,
        "smoke_selection_rule": SMOKE_SELECTION_RULE,
        "smoke_item_ids": list(SMOKE_ITEM_IDS),
        "forbidden_splits": list(FORBIDDEN_SPLITS),
        "caption_strategy": CAPTION_STRATEGY,
        "smoke_style_phrase": SMOKE_STYLE_PHRASE,
        "validation_cases": [
            {"id": c.id, "prompt_id": c.prompt_id} for c in VALIDATION_CASES
        ],
        "validation_seeds": list(VALIDATION_SEEDS),
        "validation_lora_weights": list(VALIDATION_LORA_WEIGHTS),
    }


def kit_fingerprint() -> str:
    payload = json.dumps(canonical_kit(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    print(json.dumps(canonical_kit(), indent=2))
    print(f"\nfingerprint: {kit_fingerprint()}")
