"""Unit tests for the Prototype 2 Phase-1 runner's pure helpers.

Importable without a GPU: `reference_conditioning` imports torch, diffusers,
transformers and PIL only inside the functions that need them, so the run-plan
arithmetic and the reference preprocessing geometry are testable on CPU.

These cover the parts that decide what gets measured. A wrong level plan or a
wrong crop would not raise - it would silently produce a clean-looking results
file describing the wrong experiment.
"""

import pytest

from ml.inference import reference_conditioning as rc
from ml.inference import reference_schema as rs


# --- the run plan ------------------------------------------------------------


def test_text_only_has_a_single_level_even_when_a_sweep_is_requested():
    """The control arm owns no reference-strength parameter, so it has no sweep
    values. Asking for one must yield the single 'none' level rather than a
    KeyError - EXP-010 runs the baseline through this same entry point."""
    assert rc.resolve_levels("text-only", "sweep") == [("none", None)]
    assert rc.resolve_levels("text-only", "medium") == [("none", None)]


def test_sweep_labels_are_derived_through_the_same_table_as_named_levels():
    """The sweep must not label its own points: reusing `level_for_value` is what
    keeps img2img's inverted axis from being flipped in a chart."""
    img2img = rc.resolve_levels("img2img", "sweep")
    assert [value for _, value in img2img] == list(rs.SWEEP_VALUES["img2img"])
    # Lowest strength = strongest reference influence.
    assert img2img[-1] == ("strong", 0.30)
    assert img2img[0] == ("weak", 0.90)

    ip_adapter = rc.resolve_levels("ip-adapter", "sweep")
    assert ip_adapter[-1] == ("strong", 1.00)
    assert ip_adapter[0] == ("weak", 0.20)


def test_named_levels_resolve_against_the_method_own_table():
    assert rc.resolve_levels("ip-adapter", "medium") == [("medium", 0.55)]
    assert rc.resolve_levels("img2img", "weak,medium,strong") == [
        ("weak", 0.85),
        ("medium", 0.65),
        ("strong", 0.40),
    ]


def test_an_unknown_level_name_fails_loudly_rather_than_silently_running_something_else():
    with pytest.raises(SystemExit):
        rc.resolve_levels("ip-adapter", "very-strong")
    with pytest.raises(SystemExit):
        rc.resolve_levels("img2img", "none")


# --- reference preprocessing geometry ----------------------------------------


def _solid(width: int, height: int):
    from PIL import Image

    return Image.new("RGB", (width, height), (120, 40, 200))


def test_img2img_preprocessing_produces_exactly_the_target_geometry():
    """img2img forces the reference into the output resolution; the output image
    size is the init image's size, so this must be exact, not approximate."""
    for source in ((690, 1024), (4000, 2980), (1024, 699), (512, 1536)):
        prepared, note = rc.preprocess_for_img2img(_solid(*source), 512, 1536)
        assert prepared.size == (512, 1536), f"{source} did not reach the deck geometry"
        assert "centre-crop" in note and "LANCZOS" in note


def test_img2img_crop_discards_exactly_the_recorded_retained_fraction():
    """The retained-area fraction reported per run must describe the crop that
    actually happened, not an independent estimate of it."""
    source_width, source_height = 1024, 699
    image = _solid(source_width, source_height)
    prepared, _ = rc.preprocess_for_img2img(image, 512, 1536)
    assert prepared.size == (512, 1536)

    # Re-derive the crop the function performs and compare with the registry
    # arithmetic used in the results rows.
    target_aspect = 512 / 1536
    crop_width = round(source_height * target_aspect)
    measured = (crop_width * source_height) / (source_width * source_height)
    assert measured == pytest.approx(
        rs.retained_area_fraction(source_width, source_height, 512, 1536), abs=1e-3
    )


def test_adapter_preprocessing_never_changes_the_aspect_ratio():
    """IP-Adapter's advertised advantage is that output geometry is untouched, so
    the reference must not be cropped to the deck aspect on this path."""
    image = _solid(4000, 2980)
    prepared, note = rc.preprocess_for_adapter(image)
    assert max(prepared.size) == rc.MAX_REFERENCE_LONG_SIDE
    assert prepared.width / prepared.height == pytest.approx(4000 / 2980, abs=1e-3)
    assert "centre-crop 224" in note


def test_adapter_preprocessing_leaves_references_within_the_bound_untouched():
    """R1 is 690x1024: its long side sits exactly on the bound, so it is passed
    at native size and the note records that no resampling happened."""
    image = _solid(690, 1024)
    prepared, note = rc.preprocess_for_adapter(image)
    assert prepared.size == (690, 1024)
    assert "native size 690x1024" in note
    assert "LANCZOS" not in note


def test_the_long_side_bound_applies_to_the_tall_deck_aspect_too():
    """R2 and R4 are 512x1536, so the bound does fire on them - the reduction is
    recorded in the per-run note rather than passing silently."""
    prepared, note = rc.preprocess_for_adapter(_solid(512, 1536))
    assert prepared.size == (341, 1024)
    assert prepared.width / prepared.height == pytest.approx(512 / 1536, abs=1e-3)
    assert "long side bounded 512x1536 -> 341x1024" in note


# --- failure recording -------------------------------------------------------


def test_an_error_with_no_message_still_records_something_usable():
    """Some CUDA and safetensors errors carry an empty str(); taking
    splitlines()[0] would raise inside the handler and destroy the failure row
    that this project is required to keep."""
    assert "RuntimeError" in rc._first_line(RuntimeError(""))
    assert rc._first_line(ValueError("first line\nsecond line")) == "first line"
    assert len(rc._first_line(ValueError("x" * 1000))) == 400
