"""The deployment manifest must state what the code actually requires.

A deployment document that drifts from the code is worse than no document: it
sends someone restoring a machine to the wrong path, or has them verify a hash
the service will not accept. `.env.example` had drifted exactly that way and
nobody noticed until M8, so this manifest is checked rather than trusted.

Everything here is derived from `apps/api/styles.py`, which stays the single
source of truth. The markdown is the copy, and the copy is what gets audited.
"""

import re
from pathlib import Path

import pytest

from apps.api.styles import ADAPTER_FILENAME, PRODUCTION_STYLES

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "docs" / "deployment" / "weights-manifest.md"


@pytest.fixture(scope="module")
def manifest_text() -> str:
    assert MANIFEST.is_file(), f"{MANIFEST} is missing"
    return MANIFEST.read_text(encoding="utf-8")


def test_every_production_style_appears_with_its_run_and_step(manifest_text):
    for style in PRODUCTION_STYLES:
        assert style.key in manifest_text, f"{style.key} is not documented"
        assert style.run_id in manifest_text, f"{style.run_id} is not documented"


def test_every_recorded_sha256_appears_verbatim(manifest_text):
    for style in PRODUCTION_STYLES:
        assert style.sha256 in manifest_text, (
            f"the sha256 for {style.key} in the manifest does not match "
            f"apps/api/styles.py ({style.sha256})"
        )


def test_no_wrong_hash_is_documented(manifest_text):
    """The reverse direction: a stale hash left behind would be worse than none."""
    known = {style.sha256 for style in PRODUCTION_STYLES}
    found = set(re.findall(r"\b[0-9a-f]{64}\b", manifest_text))
    assert found <= known, f"the manifest documents unknown sha256 values: {sorted(found - known)}"
    assert found == known, "not every production hash is documented"


def test_every_documented_path_is_the_path_the_service_resolves(manifest_text):
    """A path that looks right but is not the one `adapter_path` builds is a trap."""
    for style in PRODUCTION_STYLES:
        expected = style.adapter_path(Path("ROOT"))
        relative = expected.relative_to(Path("ROOT")).as_posix()
        assert relative in manifest_text, (
            f"the manifest does not contain the real resolved path for {style.key}: {relative}"
        )
        assert relative.endswith(ADAPTER_FILENAME)


def test_the_recorded_byte_size_is_documented(manifest_text):
    sizes = {style.size_bytes for style in PRODUCTION_STYLES}
    assert len(sizes) == 1, "the styles no longer share one size; update the manifest wording"
    size = next(iter(sizes))
    # Written with thin spaces for readability, so compare on digits only.
    digits_only = re.sub(r"[\s\u202f\u00a0]", "", manifest_text)
    assert str(size) in digits_only, f"the manifest does not state the {size} byte size"


def test_the_manifest_documents_the_configurable_root_not_a_private_path(manifest_text):
    """The reproducible mechanism must not be somebody's absolute drive path."""
    assert "CHECKPOINT_ROOT" in manifest_text

    # A concrete personal path would make the instructions unusable elsewhere.
    assert "C:\\Users\\kylia" not in manifest_text
    assert "C:\\Expert Lab" not in manifest_text


def test_the_manifest_states_that_the_checkpoints_are_unregenerable(manifest_text):
    """R14 is a reproducibility limitation and must be stated, not implied."""
    assert "R14" in manifest_text
    lowered = manifest_text.lower()
    assert "cannot be regenerated" in lowered or "cannot be rebuilt" in lowered
    assert "never to retrain" in lowered or "never retrain" in lowered


def test_the_manifest_does_not_promise_a_public_download(manifest_text):
    """These three files are not downloadable, and saying otherwise would strand
    anyone who followed the instructions."""
    lowered = manifest_text.lower()
    assert "not from a public download" in lowered
