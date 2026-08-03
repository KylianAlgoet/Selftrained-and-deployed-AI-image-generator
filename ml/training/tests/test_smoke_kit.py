"""Guards for the frozen Prototype 3 smoke-test kit and its manifest.

The point of these tests is that "frozen" and "no holdout contamination" are
*proven from dataset-v1*, not asserted by the smoke manifest about itself. A
manifest that vouches for its own split column would catch nothing.
"""

import ast
import csv
import re
import sys
from pathlib import Path

import pytest

from ml.training import smoke_kit

REPO = Path(__file__).resolve().parents[3]
DATASET_MANIFEST = REPO / "data" / "manifests" / "dataset-v1.csv"
SMOKE_MANIFEST = REPO / smoke_kit.SMOKE_MANIFEST_PATH

# Recorded 2026-08-04 from the kit as first frozen in Prototype 3.
# Only update this together with a documented decision + process-log entry.
FROZEN_FINGERPRINT = "a8052f44045c1511d72689438a65216efd044fe7b494978fae59daac0b8e6470"

NOTE_RE = re.compile(r"seed=(\d+), palette_index=(\d+), shape_count=(\d+)")


@pytest.fixture(scope="module")
def dataset_rows():
    return list(csv.DictReader(DATASET_MANIFEST.open(encoding="utf-8")))


@pytest.fixture(scope="module")
def smoke_rows():
    return list(csv.DictReader(SMOKE_MANIFEST.open(encoding="utf-8")))


# --- the freeze itself -------------------------------------------------------


def test_kit_fingerprint_is_frozen():
    assert smoke_kit.kit_fingerprint() == FROZEN_FINGERPRINT, (
        "The Prototype 3 smoke kit changed. Any training run compared across this change "
        "is no longer comparable. If the change is intended, record a decision and "
        "process-log entry, then update FROZEN_FINGERPRINT deliberately."
    )


def test_fingerprint_is_sensitive_to_change(monkeypatch):
    """A fingerprint that never changes would be a useless lock."""
    monkeypatch.setattr(smoke_kit, "VALIDATION_SEEDS", (42,))
    assert smoke_kit.kit_fingerprint() != FROZEN_FINGERPRINT


def test_subset_is_the_declared_size():
    assert len(smoke_kit.SMOKE_ITEM_IDS) == smoke_kit.SMOKE_SUBSET_SIZE == 12
    assert len(set(smoke_kit.SMOKE_ITEM_IDS)) == 12, "duplicate id in the frozen subset"


# --- the selection rule really produces the frozen subset --------------------


def test_selection_rule_reproduces_the_frozen_ids(dataset_rows):
    """Re-derive the subset from dataset-v1; catches an edit here AND upstream."""
    pool = [
        r for r in dataset_rows if r["style"] == smoke_kit.SMOKE_STYLE and r["split"] == "train"
    ]
    pool.sort(key=lambda r: r["id"])
    derived = tuple(r["id"] for r in pool[: smoke_kit.SMOKE_SUBSET_SIZE])
    assert derived == smoke_kit.SMOKE_ITEM_IDS


def test_manifest_matches_the_frozen_ids_in_order(smoke_rows):
    assert tuple(r["id"] for r in smoke_rows) == smoke_kit.SMOKE_ITEM_IDS


# --- holdout / validation contamination --------------------------------------


def test_no_smoke_item_comes_from_val_or_holdout(dataset_rows):
    """Proven against dataset-v1, not against the smoke manifest's own column."""
    by_id = {r["id"]: r for r in dataset_rows}
    for item_id in smoke_kit.SMOKE_ITEM_IDS:
        assert item_id in by_id, f"{item_id} is not in dataset-v1 at all"
        split = by_id[item_id]["split"]
        assert split not in smoke_kit.FORBIDDEN_SPLITS, f"{item_id} leaked from split {split!r}"
        assert split == "train", f"{item_id} has unexpected split {split!r}"


def test_prototype_2_reference_items_are_not_in_the_training_subset(dataset_rows):
    """Prototype 2's references come from the holdout split; they must stay unseen."""
    holdout_ids = {r["id"] for r in dataset_rows if r["split"] == "holdout"}
    assert holdout_ids, "dataset-v1 has no holdout split; the guard would be vacuous"
    assert not (holdout_ids & set(smoke_kit.SMOKE_ITEM_IDS))


# --- provenance: the manifest agrees with dataset-v1 byte-for-byte -----------


def test_manifest_rows_match_dataset_v1(dataset_rows, smoke_rows):
    by_id = {r["id"]: r for r in dataset_rows}
    for row in smoke_rows:
        source = by_id[row["id"]]
        assert row["sha256"] == source["sha256"], f"{row['id']} sha256 drifted from dataset-v1"
        assert row["filename"] == source["filename"]
        assert row["style"] == source["style"] == smoke_kit.SMOKE_STYLE
        assert row["split"] == source["split"] == "train"
        assert row["width"] == source["width"]
        assert row["height"] == source["height"]
        assert row["caption"] == source["caption"], (
            f"{row['id']} caption is not the dataset-v1 caption verbatim, which is the "
            "frozen caption strategy"
        )


def test_every_item_is_the_native_deck_format(smoke_rows):
    """The sources are 512x1536; the 512x512 arm crops them, and that transform is
    a recorded field of the run rather than a property of the data."""
    for row in smoke_rows:
        assert (row["width"], row["height"]) == ("512", "1536")


def test_source_paths_point_into_the_gitignored_raw_tree(smoke_rows):
    for row in smoke_rows:
        assert row["source_path"].startswith("data/raw/")
        assert row["source_path"].endswith(row["filename"])


def test_every_row_records_an_inclusion_reason(smoke_rows):
    for row in smoke_rows:
        assert row["inclusion_reason"].strip(), f"{row['id']} has no inclusion reason"


# --- caption strategy --------------------------------------------------------


def test_captions_use_the_frozen_style_phrase(smoke_rows):
    from ml.dataset.captions import STYLE_PHRASES

    assert STYLE_PHRASES[smoke_kit.SMOKE_STYLE] == smoke_kit.SMOKE_STYLE_PHRASE, (
        "the dataset style phrase moved away from the frozen smoke-kit copy"
    )
    for row in smoke_rows:
        assert row["caption"].startswith(smoke_kit.SMOKE_STYLE_PHRASE)


def test_no_trigger_token_was_introduced(smoke_rows):
    """M5 uses dataset captions verbatim; trigger-token design is a Prototype 4 decision."""
    assert "no trigger token" in smoke_kit.CAPTION_STRATEGY
    for row in smoke_rows:
        assert not re.search(r"\bsks\b|<[^>]+>|\bohwx\b", row["caption"], re.IGNORECASE)


def test_no_caption_reintroduces_the_retracted_comic_label(smoke_rows):
    """Regression guard tied to the 2026-07-30 style relabel."""
    for row in smoke_rows:
        assert "comic" not in row["caption"].lower()
        assert "halftone" not in row["caption"].lower()


# --- subset spread -----------------------------------------------------------


def test_subset_covers_all_palettes_and_shape_counts(dataset_rows):
    """A silent rebuild must not collapse the subset onto one palette."""
    by_id = {r["id"]: r for r in dataset_rows}
    palettes, shapes = set(), set()
    for item_id in smoke_kit.SMOKE_ITEM_IDS:
        note = NOTE_RE.search(by_id[item_id]["notes"] or "")
        assert note, f"{item_id} has no parseable generator note"
        palettes.add(int(note.group(2)))
        shapes.add(int(note.group(3)))
    assert len(palettes) == 6, f"palette coverage dropped to {sorted(palettes)}"
    assert len(shapes) == 6, f"shape-count coverage dropped to {sorted(shapes)}"


# --- validation kit ----------------------------------------------------------


def test_validation_prompts_exist_in_the_frozen_evaluation_kit():
    """Comparability with Prototype 1 and 2 depends on these being the same prompts."""
    from ml.evaluation import prompt_kit

    for case in smoke_kit.VALIDATION_CASES:
        assert prompt_kit.prompt_by_id(case.prompt_id) is not None


def test_validation_covers_the_trained_style_and_a_style_free_control():
    prompt_ids = {c.prompt_id for c in smoke_kit.VALIDATION_CASES}
    assert "P2-geo" in prompt_ids, "the trained style must be validated"
    assert "P5-control" in prompt_ids, "a style-free control separates a style effect from a global shift"


def test_validation_seeds_are_drawn_from_the_frozen_kit():
    from ml.evaluation import prompt_kit

    assert set(smoke_kit.VALIDATION_SEEDS) <= set(prompt_kit.SEEDS)
    assert 42 in smoke_kit.VALIDATION_SEEDS


def test_lora_weights_bracket_inactive_and_active():
    assert smoke_kit.LORA_WEIGHT_LOWER_BOUND == 0.0
    assert smoke_kit.LORA_WEIGHT_ACTIVE == 1.0
    assert smoke_kit.VALIDATION_LORA_WEIGHTS == (0.0, 1.0)


# --- import boundary ---------------------------------------------------------


BANNED_TOP_LEVEL_IMPORTS = ("torch", "diffusers", "transformers", "peft", "PIL", "accelerate")


def test_smoke_kit_imports_no_torch_or_evaluation_model():
    """The kit must stay importable on any machine without a GPU, and must never
    drag a metric encoder into a process whose VRAM figures are being measured.

    Parsed from the AST rather than scanned as text: prose mentioning torch is
    fine, an actual `import torch` is not.
    """
    module = sys.modules[smoke_kit.__name__]
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])

    offenders = imported & set(BANNED_TOP_LEVEL_IMPORTS)
    assert not offenders, f"smoke_kit must not import {sorted(offenders)}"
