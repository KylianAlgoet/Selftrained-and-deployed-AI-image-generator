"""The frozen Prototype 4 (M6) style-learning kit.

Everything a style training run is allowed to vary is fixed here BEFORE any GPU
work: which styles are trained, in what order, with which trigger token, under
which caption strategy, and against which validation prompts, seeds and weights.

Deliberately free of torch/diffusers/PIL imports, exactly like `smoke_kit` and
`lora_schema`, so the whole kit is unit-testable without a GPU. The CLIP token-id
sequences below are RECORDED CONSTANTS, verified against the pinned tokenizer by
a test rather than recomputed at import time.

Four things are frozen:

1. **The styles and their order** - `minimal-geometric` first, because it is the
   only style already proven to train (M5), the only one whose sources are
   deck-shaped, and the only one free of both known dataset contaminants.
2. **One trigger token per style.** Chosen over a shared project token because a
   shared token cannot separate styles inside the multi-style LoRA, which would
   make RQ5 unanswerable.
3. **The caption strategy** - style-only, no content phrase. See CAPTION_MODE.
4. **The validation prompts, seeds and adapter weights**, drawn from the frozen
   evaluation kit (`ml.evaluation.prompt_kit`, fingerprint c40749bc...) so
   Prototype 4 stays comparable with Prototypes 1-3.

`kit_fingerprint()` hashes the whole thing and a pytest asserts it against a
recorded constant, the same protection `prompt_kit` and `smoke_kit` carry.
"""

import hashlib
import json
from dataclasses import dataclass

# --- Pinned tokenizer facts --------------------------------------------------

# Read from the SD 1.5 tokenizer at revision 451f4fe1... on 2026-08-04. A test
# asserts these still hold, which is what makes "the vocabulary is unchanged" a
# check rather than a promise.
TOKENIZER_VOCAB_SIZE = 49408
TOKENIZER_MODEL_MAX_LENGTH = 77

# NO NEW VOCABULARY ENTRIES ARE EVER ADDED.
#
# The text encoder is frozen for the whole of M6 (DR-009), so an added embedding
# would never receive a gradient and would behave as untrained noise for the rest
# of the project. The triggers below are therefore ordinary BPE token SEQUENCES
# that already exist in the vocabulary - nothing is registered, resized or
# extended.
ADDS_TOKENIZER_VOCABULARY = False

# --- Trigger tokens ----------------------------------------------------------


@dataclass(frozen=True)
class StyleSpec:
    key: str
    trigger: str
    # Recorded, not recomputed: a test compares these against the live tokenizer.
    trigger_token_ids: tuple[int, ...]
    trigger_token_pieces: tuple[str, ...]
    order: int
    note: str


# The first candidate family - `dfgeo` / `dfukiyo` / `dfposter` - was REJECTED on
# measured tokenizer evidence, not on taste:
#
#   dfukiyo  -> ['d', 'fu', 'ki', 'yo</w>']  4 pieces, and it loses the shared
#               'df' prefix the other two had, so the family was not even
#               internally consistent.
#   dfposter -> ['df', 'poster</w>'] where 'poster</w>' ALSO appears inside its
#               own style phrase ("retro silkscreen poster style") and across the
#               caption corpus - exactly the ordinary-word collision a trigger
#               must avoid.
#   xuki     -> ['x', 'uki</w>'] collided too: several ukiyo-e captions contain
#               the literal words "uki e", so 'uki</w>' is already in the corpus.
#
# The selected family is uniform: every trigger is exactly TWO pieces, all share
# the leading 'x' piece, and NO piece of any trigger appears anywhere in the
# dataset-v1 captions, the style phrases, or the frozen prompt kit.
STYLES: tuple[StyleSpec, ...] = (
    StyleSpec(
        key="minimal-geometric",
        trigger="xgeo",
        trigger_token_ids=(87, 11604),
        trigger_token_pieces=("x", "geo</w>"),
        order=1,
        note=(
            "trained first: the only style already proven to train (M5 EXP-016), the only one "
            "whose sources are all exactly 1:3, project-original licence, and free of both the "
            "frame and pseudo-text contaminants. Highest memorisation risk in the set, though: "
            "44 near-uniform synthetic images with only ~6 distinct dataset captions"
        ),
    ),
    StyleSpec(
        key="ukiyo-e",
        trigger="xkyo",
        trigger_token_ids=(87, 6281),
        trigger_token_pieces=("x", "kyo</w>"),
        order=2,
        note=(
            "trained second: most train items (44), cleanest licence (CC0), best captions of the "
            "two archival styles, and no frame or pseudo-text problem. Sources are NOT deck-shaped "
            "(median 1.33 h/w, 15 of 44 landscape), which is why training is at 512x512"
        ),
    ),
    StyleSpec(
        key="retro-poster",
        trigger="xpst",
        trigger_token_ids=(87, 12692),
        trigger_token_pieces=("x", "pst</w>"),
        order=3,
        note=(
            "trained last: carries every known risk at once - framed/matted scans, display "
            "typography, 8 of 36 landscape, and 20 of 41 captions that are play-title "
            "attributions rather than descriptions. Attempted rather than assumed to fail, "
            "because H4 is a real hypothesis either way"
        ),
    ),
)

STYLE_ORDER: tuple[str, ...] = tuple(s.key for s in sorted(STYLES, key=lambda s: s.order))
LEAD_STYLE = STYLE_ORDER[0]

# --- Caption strategy --------------------------------------------------------

# Style-only: the trigger, the style phrase, and the fixed suffix. No content
# phrase at all.
#
# Justified by the caption audit, not by preference. dataset-v1's content phrases
# are archive metadata rather than visual description: 20 of 41 `retro-poster`
# captions are play-title attributions ("alien corn by sidney howard"), 9 of 55
# `ukiyo-e` captions are truncated mid-phrase ("...from the series eight views
# of"), and `minimal-geometric` has only ~6 distinct phrases across 52 items.
# Training a style LoRA on those teaches the trigger proper nouns.
#
# This is a hypothesis under test, not an assumption: EXP-023 retrains the lead
# style on the dataset-v1 captions verbatim, changing nothing else, and the two
# arms are scored blind.
CAPTION_MODE_STYLE_ONLY = "style-only"
CAPTION_MODE_VERBATIM = "dataset-v1-verbatim"
CAPTION_MODES: tuple[str, ...] = (CAPTION_MODE_STYLE_ONLY, CAPTION_MODE_VERBATIM)

CAPTION_SUFFIX = "skateboard decal artwork"


def style_by_key(key: str) -> StyleSpec:
    for style in STYLES:
        if style.key == key:
            return style
    raise KeyError(f"unknown style {key!r}; expected one of {[s.key for s in STYLES]}")


def build_training_caption(style_key: str, style_phrase: str) -> str:
    """`<trigger> <style phrase> skateboard decal artwork`.

    `style_phrase` is passed in rather than imported so this module stays free of
    every other import; callers pass `ml.dataset.captions.STYLE_PHRASES[key]`, and
    a test asserts the phrase actually used matches that table.
    """
    trigger = style_by_key(style_key).trigger
    phrase = " ".join(style_phrase.split()).strip()
    if not phrase:
        raise ValueError("style phrase must not be empty")
    return f"{trigger} {phrase} {CAPTION_SUFFIX}"


# --- Dataset-size experiment (RQ4) -------------------------------------------

# Nested subsets of the LEAD style's train split: 12 subset of 24 subset of 44.
# Deterministic, no RNG - sort by id ascending and take the first N, the same rule
# the M5 smoke subset used.
SIZE_ARM_COUNTS: tuple[int, ...] = (12, 24)
SIZE_ARM_SELECTION_RULE = "style train split, sorted by id ascending, first N (no RNG)"

# The confound is declared here, in the code, before any result exists.
#
# All three arms run the SAME 300 optimizer steps, so the smaller sets present
# each item far more often: 12 images -> 25.0x, 24 -> 12.5x, 44 -> ~6.8x. This
# measures TRAINING-SET SIZE AT EQUAL COMPUTE, deliberately conflated with
# repetition. It is NOT an equal-epochs comparison, it estimates the effect for
# `minimal-geometric` only, and it must not be generalised to the other styles.
# Per-item presentation counts are recorded per run so the confound stays visible.
SIZE_ARM_LIMITATION = (
    "equal compute (300 steps) across 12/24/44 images means each item is presented 25.0x, "
    "12.5x and ~6.8x respectively; this measures set size at equal compute, not at equal "
    "epochs, for minimal-geometric only, and does not establish a universal minimum"
)

# --- Pilot configuration -----------------------------------------------------

PILOT_STEPS = 300
PILOT_CHECKPOINT_STEPS: tuple[int, ...] = (150, 300)

# Full-run step count is NOT chosen here. It is Kylian's decision at gate 1, from
# a pre-declared band. Recording the band rather than a value is deliberate.
FULL_RUN_STEP_BAND: tuple[int, int] = (600, 1500)

# --- Validation --------------------------------------------------------------


@dataclass(frozen=True)
class ValidationPrompt:
    id: str
    role: str
    # Filled per style at build time; `{trigger}` and `{phrase}` are substituted.
    template: str
    intent: str


# The two prompts used in the SMALL pilot matrix. Kept to two on purpose: the
# pilot matrix exists to support one human decision, not to pre-empt the final
# comparison.
PILOT_PROMPTS: tuple[ValidationPrompt, ...] = (
    ValidationPrompt(
        id="VP1-style",
        role="style-matching",
        template="{trigger} {phrase} skateboard decal artwork, a coiled serpent",
        intent="does the trigger produce the trained style on a subject the style can carry",
    ),
    ValidationPrompt(
        id="VP2-shared",
        role="shared-cross-style",
        template="{trigger} {phrase} skateboard decal artwork, a mountain and a rising sun",
        intent=(
            "identical subject across all three styles, so style differences are attributable "
            "to the LoRA rather than to the prompt"
        ),
    ),
)

PILOT_SEEDS: tuple[int, ...] = (42, 1337)
PILOT_LORA_WEIGHTS: tuple[float, ...] = (0.7, 1.0)

# The FINAL matrix (Phase B) runs only on checkpoints Kylian approves at gate 1.
FINAL_LORA_WEIGHTS: tuple[float, ...] = (0.0, 0.4, 0.7, 1.0)
FINAL_SEEDS: tuple[int, ...] = (42, 1337, 2026)

# Hard caps declared before execution, so the matrices cannot quietly grow.
PILOT_MATRIX_MAX_GENERATIONS = 108
FINAL_MATRIX_MAX_GENERATIONS = 432

# --- Run budget --------------------------------------------------------------

# 3 pilots + 1 caption A/B + 2 size arms + 3 approved full runs + 1 multi-style
# + <=2 contingency. No thirteenth run without explicit approval.
MAX_TRAINING_RUNS = 12

# --- Read-only guarantee -----------------------------------------------------

# dataset-v1 is opened read-only for the whole of M6. A test asserts the file is
# byte-identical to this hash at every point, so "we did not modify the dataset"
# is verifiable rather than asserted.
DATASET_V1_SHA256 = "cd18cbb05307b2534137fd1b22a9d51943ff568d7124132b07e5d0f866477ac0"

# --- Fingerprint --------------------------------------------------------------


def canonical_kit() -> dict:
    """Order-stable, serialisable view of the kit - the input to the fingerprint."""
    return {
        "tokenizer_vocab_size": TOKENIZER_VOCAB_SIZE,
        "tokenizer_model_max_length": TOKENIZER_MODEL_MAX_LENGTH,
        "adds_tokenizer_vocabulary": ADDS_TOKENIZER_VOCABULARY,
        "styles": [
            {
                "key": s.key,
                "trigger": s.trigger,
                "trigger_token_ids": list(s.trigger_token_ids),
                "order": s.order,
            }
            for s in sorted(STYLES, key=lambda s: s.order)
        ],
        "caption_modes": list(CAPTION_MODES),
        "caption_suffix": CAPTION_SUFFIX,
        "size_arm_counts": list(SIZE_ARM_COUNTS),
        "size_arm_selection_rule": SIZE_ARM_SELECTION_RULE,
        "pilot_steps": PILOT_STEPS,
        "pilot_checkpoint_steps": list(PILOT_CHECKPOINT_STEPS),
        "full_run_step_band": list(FULL_RUN_STEP_BAND),
        "pilot_prompts": [{"id": p.id, "template": p.template} for p in PILOT_PROMPTS],
        "pilot_seeds": list(PILOT_SEEDS),
        "pilot_lora_weights": list(PILOT_LORA_WEIGHTS),
        "final_lora_weights": list(FINAL_LORA_WEIGHTS),
        "final_seeds": list(FINAL_SEEDS),
        "max_training_runs": MAX_TRAINING_RUNS,
        "dataset_v1_sha256": DATASET_V1_SHA256,
    }


def kit_fingerprint() -> str:
    payload = json.dumps(canonical_kit(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    print(json.dumps(canonical_kit(), indent=2))
    print(f"\nfingerprint: {kit_fingerprint()}")
