"""Guards for the frozen Prototype 4 style kit and its per-style manifests.

The load-bearing tests here are the ones that prove things *against dataset-v1*
rather than against the new manifests' own columns, and the ones that assert the
recorded CLIP token ids match the live tokenizer. A manifest vouching for itself
would catch nothing, and a recorded token id nobody checks is just a comment.
"""

import ast
import csv
import sys
from pathlib import Path

import pytest

from ml.dataset.captions import STYLE_PHRASES
from ml.dataset.hashing import sha256_file
from ml.training import style_kit

REPO = Path(__file__).resolve().parents[3]
DATASET_MANIFEST = REPO / "data" / "manifests" / "dataset-v1.csv"
MANIFEST_DIR = REPO / "data" / "manifests"

# Recorded 2026-08-04 from the kit as first frozen in Prototype 4.
# Only update this together with a documented decision + process-log entry.
FROZEN_FINGERPRINT = "fc11d8289a88760745a6228d94c498d1ed95648a6c38f80c1a88601de202a58b"


@pytest.fixture(scope="module")
def dataset_rows():
    return list(csv.DictReader(DATASET_MANIFEST.open(encoding="utf-8")))


def style_rows(style: str, suffix: str = "") -> list[dict]:
    path = MANIFEST_DIR / f"style-{style}-p4{suffix}.csv"
    return list(csv.DictReader(path.open(encoding="utf-8")))


# --- the freeze --------------------------------------------------------------


def test_kit_fingerprint_is_frozen():
    assert style_kit.kit_fingerprint() == FROZEN_FINGERPRINT, (
        "The Prototype 4 style kit changed. Runs compared across this change are no longer "
        "comparable. If intended, record a decision and process-log entry, then update "
        "FROZEN_FINGERPRINT deliberately."
    )


def test_fingerprint_is_sensitive_to_change(monkeypatch):
    monkeypatch.setattr(style_kit, "PILOT_STEPS", style_kit.PILOT_STEPS + 1)
    assert style_kit.kit_fingerprint() != FROZEN_FINGERPRINT


# --- dataset v1 is read-only -------------------------------------------------


def test_dataset_v1_is_byte_identical_to_the_recorded_hash():
    """M6 must not modify dataset v1. Verified, not asserted in prose."""
    assert sha256_file(DATASET_MANIFEST) == style_kit.DATASET_V1_SHA256


# --- trigger tokens ----------------------------------------------------------


def test_every_style_has_a_unique_trigger():
    triggers = [s.trigger for s in style_kit.STYLES]
    assert len(triggers) == len(set(triggers)) == 3


def test_triggers_are_uniform_two_piece_sequences():
    """A trigger split into four pieces would be a weaker, inconsistent signal."""
    for spec in style_kit.STYLES:
        assert len(spec.trigger_token_ids) == 2, f"{spec.trigger} is not 2 pieces"
        assert len(spec.trigger_token_pieces) == 2


def test_triggers_share_a_leading_piece():
    firsts = {s.trigger_token_ids[0] for s in style_kit.STYLES}
    assert len(firsts) == 1, "the trigger family is not internally consistent"


def test_no_trigger_piece_appears_anywhere_in_the_caption_corpus(dataset_rows):
    """The collision check that rejected `dfposter` and `xuki`.

    `poster</w>` sits inside its own style phrase, and `uki</w>` appears in ukiyo-e
    captions containing the literal words "uki e".
    """
    pytest.importorskip("transformers")
    from transformers import CLIPTokenizer

    from ml.evaluation import prompt_kit

    tok = CLIPTokenizer.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        subfolder="tokenizer",
        revision="451f4fe16113bff5a5d2269ed5ad43b0592e9a14",
    )
    corpus: set[int] = set()
    texts = list(STYLE_PHRASES.values())
    texts += [p.text for p in prompt_kit.PROMPTS]
    texts.append(prompt_kit.NEGATIVE_PROMPT)
    texts += [r["caption"] for r in dataset_rows]
    for text in texts:
        corpus.update(tok(text, add_special_tokens=False).input_ids)

    for spec in style_kit.STYLES:
        overlap = set(spec.trigger_token_ids) & corpus
        assert not overlap, f"{spec.trigger} collides with corpus tokens {sorted(overlap)}"


def test_recorded_token_ids_match_the_live_tokenizer():
    """A recorded constant nobody checks is just a comment."""
    pytest.importorskip("transformers")
    from transformers import CLIPTokenizer

    tok = CLIPTokenizer.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        subfolder="tokenizer",
        revision="451f4fe16113bff5a5d2269ed5ad43b0592e9a14",
    )
    for spec in style_kit.STYLES:
        ids = tuple(tok(spec.trigger, add_special_tokens=False).input_ids)
        assert ids == spec.trigger_token_ids, f"{spec.trigger} ids drifted: {ids}"


def test_tokenizer_vocabulary_is_unchanged():
    """No new vocabulary entries: the text encoder is frozen, so an added
    embedding would never be trained and would behave as noise."""
    pytest.importorskip("transformers")
    from transformers import CLIPTokenizer

    tok = CLIPTokenizer.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        subfolder="tokenizer",
        revision="451f4fe16113bff5a5d2269ed5ad43b0592e9a14",
    )
    assert style_kit.ADDS_TOKENIZER_VOCABULARY is False
    assert len(tok) == style_kit.TOKENIZER_VOCAB_SIZE
    assert tok.model_max_length == style_kit.TOKENIZER_MODEL_MAX_LENGTH


def test_training_captions_fit_well_inside_the_prompt_limit():
    pytest.importorskip("transformers")
    from transformers import CLIPTokenizer

    tok = CLIPTokenizer.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        subfolder="tokenizer",
        revision="451f4fe16113bff5a5d2269ed5ad43b0592e9a14",
    )
    for spec in style_kit.STYLES:
        caption = style_kit.build_training_caption(spec.key, STYLE_PHRASES[spec.key])
        n = len(tok(caption).input_ids)
        assert n < style_kit.TOKENIZER_MODEL_MAX_LENGTH, f"{caption!r} is {n} tokens"


# --- caption strategy --------------------------------------------------------


def test_training_caption_is_style_only():
    caption = style_kit.build_training_caption("minimal-geometric", STYLE_PHRASES["minimal-geometric"])
    assert caption == "xgeo minimal geometric abstract style skateboard decal artwork"
    assert "composition of" not in caption


def test_style_phrases_come_from_the_dataset_table():
    for spec in style_kit.STYLES:
        assert STYLE_PHRASES[spec.key] in style_kit.build_training_caption(
            spec.key, STYLE_PHRASES[spec.key]
        )


def test_both_caption_modes_exist_because_one_is_under_test():
    assert style_kit.CAPTION_MODES == ("style-only", "dataset-v1-verbatim")


def test_unknown_style_raises():
    with pytest.raises(KeyError, match="unknown style"):
        style_kit.style_by_key("art-deco")


# --- style order -------------------------------------------------------------


def test_lead_style_is_the_one_already_proven_to_train():
    assert style_kit.LEAD_STYLE == "minimal-geometric"
    assert style_kit.STYLE_ORDER == ("minimal-geometric", "ukiyo-e", "retro-poster")


# --- manifests: proven against dataset-v1 ------------------------------------


@pytest.mark.parametrize("style,expected", [("minimal-geometric", 44), ("ukiyo-e", 44), ("retro-poster", 36)])
def test_manifest_sizes(style, expected):
    assert len(style_rows(style)) == expected


@pytest.mark.parametrize("style", ["minimal-geometric", "ukiyo-e", "retro-poster"])
def test_no_manifest_item_comes_from_val_or_holdout(style, dataset_rows):
    """Proven against dataset-v1, not against the manifest's own split column."""
    by_id = {r["id"]: r for r in dataset_rows}
    for row in style_rows(style):
        source = by_id[row["id"]]
        assert source["split"] == "train", f"{row['id']} leaked from split {source['split']!r}"


@pytest.mark.parametrize("style", ["minimal-geometric", "ukiyo-e", "retro-poster"])
def test_manifest_hashes_and_captions_match_dataset_v1(style, dataset_rows):
    by_id = {r["id"]: r for r in dataset_rows}
    for row in style_rows(style):
        source = by_id[row["id"]]
        assert row["sha256"] == source["sha256"]
        assert row["dataset_v1_caption"] == source["caption"]
        assert row["licence"] == source["licence"]


@pytest.mark.parametrize("style", ["minimal-geometric", "ukiyo-e", "retro-poster"])
def test_training_caption_is_identical_within_a_style(style):
    captions = {r["training_caption"] for r in style_rows(style)}
    assert len(captions) == 1, "style-only captions must not vary within a style"
    assert style_kit.style_by_key(style).trigger in captions.pop()


def test_holdout_items_are_in_no_training_manifest(dataset_rows):
    holdout = {r["id"] for r in dataset_rows if r["split"] == "holdout"}
    assert holdout, "no holdout split; the guard would be vacuous"
    used: set[str] = set()
    for style in style_kit.STYLE_ORDER:
        used |= {r["id"] for r in style_rows(style)}
    assert not (holdout & used)


def test_styles_do_not_share_items():
    seen: set[str] = set()
    for style in style_kit.STYLE_ORDER:
        ids = {r["id"] for r in style_rows(style)}
        assert not (ids & seen)
        seen |= ids


def test_every_row_records_an_inclusion_reason():
    for style in style_kit.STYLE_ORDER:
        for row in style_rows(style):
            assert row["inclusion_reason"].strip()


def test_every_dataset_v1_item_is_accounted_for(dataset_rows):
    """Nothing is silently dropped: used + excluded must equal the whole dataset."""
    used: set[str] = set()
    for style in style_kit.STYLE_ORDER:
        used |= {r["id"] for r in style_rows(style)}
    ledger = list(
        csv.DictReader(
            (REPO / "docs" / "evidence" / "prototype-4" / "style-manifest-exclusions.csv").open(
                encoding="utf-8"
            )
        )
    )
    excluded = {r["id"] for r in ledger}
    assert not (used & excluded)
    assert len(used | excluded) == len(dataset_rows) == 148
    for row in ledger:
        assert row["reason"].strip(), f"{row['id']} excluded with no reason"
        assert row["split"] != "train", f"{row['id']} is a train item excluded without justification"


# --- the RQ4 size arms -------------------------------------------------------


def test_size_arms_have_the_declared_counts():
    assert style_kit.SIZE_ARM_COUNTS == (12, 24)
    for n in style_kit.SIZE_ARM_COUNTS:
        assert len(style_rows(style_kit.LEAD_STYLE, f"-n{n}")) == n


def test_size_arms_are_strictly_nested():
    """n12 subset of n24 subset of n44 — otherwise the comparison is not controlled."""
    n12 = [r["id"] for r in style_rows(style_kit.LEAD_STYLE, "-n12")]
    n24 = [r["id"] for r in style_rows(style_kit.LEAD_STYLE, "-n24")]
    full = [r["id"] for r in style_rows(style_kit.LEAD_STYLE)]
    assert n12 == full[:12]
    assert n24 == full[:24]
    assert set(n12) < set(n24) < set(full)


def test_size_arms_share_the_lead_style_caption():
    caption = {r["training_caption"] for r in style_rows(style_kit.LEAD_STYLE)}
    for n in style_kit.SIZE_ARM_COUNTS:
        assert {r["training_caption"] for r in style_rows(style_kit.LEAD_STYLE, f"-n{n}")} == caption


def test_the_equal_compute_confound_is_declared_in_code():
    """The 12/24/44 arms all run 300 steps, so items are seen 25x / 12.5x / ~6.8x.
    That confound must be stated before results exist, not discovered afterwards."""
    text = style_kit.SIZE_ARM_LIMITATION.lower()
    assert "equal compute" in text
    assert "not at equal epochs" in text or "not an equal-epochs" in text
    assert "minimal-geometric" in text


# --- capped workloads --------------------------------------------------------


def test_run_and_generation_caps_match_the_approved_plan():
    assert style_kit.MAX_TRAINING_RUNS == 12
    assert style_kit.PILOT_MATRIX_MAX_GENERATIONS == 108
    assert style_kit.FINAL_MATRIX_MAX_GENERATIONS == 432


def test_pilot_matrix_stays_within_its_cap():
    arms = 6  # 3 pilots + 1 caption A/B + 2 size arms
    per_arm = (
        len(style_kit.PILOT_CHECKPOINT_STEPS)
        * len(style_kit.PILOT_LORA_WEIGHTS)
        * len(style_kit.PILOT_PROMPTS)
        * len(style_kit.PILOT_SEEDS)
    )
    base = len(style_kit.STYLE_ORDER) * len(style_kit.PILOT_PROMPTS) * len(style_kit.PILOT_SEEDS)
    assert per_arm == 16
    assert arms * per_arm + base <= style_kit.PILOT_MATRIX_MAX_GENERATIONS


def test_full_run_step_count_is_a_band_not_a_value():
    """Choosing it is Kylian's decision at gate 1, so the kit records a band."""
    assert style_kit.FULL_RUN_STEP_BAND == (600, 1500)


def test_pilot_weights_exclude_zero():
    """Weight 0.0 is the lower-bound diagnostic and belongs to the FINAL matrix;
    spending pilot generations on it would waste the small budget."""
    assert 0.0 not in style_kit.PILOT_LORA_WEIGHTS
    assert 0.0 in style_kit.FINAL_LORA_WEIGHTS


# --- import boundary ---------------------------------------------------------


def test_style_kit_imports_no_torch_or_evaluation_model():
    tree = ast.parse(Path(sys.modules[style_kit.__name__].__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    banned = {"torch", "diffusers", "transformers", "peft", "PIL", "accelerate"}
    assert not (imported & banned), f"style_kit must not import {sorted(imported & banned)}"
