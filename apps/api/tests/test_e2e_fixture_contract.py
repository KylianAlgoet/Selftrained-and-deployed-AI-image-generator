"""The Playwright fixtures must match the shapes this API really returns.

WHY THIS TEST IS THE POINT OF THE MOCKED E2E SUITE.

`apps/web/e2e/` answers every `/api/**` call from frozen fixtures. That buys a
browser-level suite that needs no GPU, no model and no weights - and it buys one
serious risk: the fixtures are a COPY of the contract, and a copy rots. Rename a
field in `schemas.py` and the backend tests still pass, the frontend tests still
pass, and the E2E suite happily keeps proving that the application works against
a response shape the server stopped sending months ago.

This test removes that failure mode by validating the fixtures against the real
Pydantic models. It is the only thing standing between "mocked E2E" and "E2E
theatre", so a fixture added there needs a case added here.

The fixtures are stored as plain JSON rather than as TypeScript literals for
exactly this reason. An earlier attempt kept them in `responses.ts` and read
them here with a regex; it broke immediately on identifiers, template strings
and spreads, and the honest conclusion was that the data should be data. The
TypeScript module now reads the same JSON at runtime, so both sides load one
file and neither parses the other's language.
"""

import json
import re
from pathlib import Path

import pytest

from apps.api.schemas import (
    ErrorResponse,
    GenerateResponse,
    GenerationProgressResponse,
    StylesResponse,
)
from apps.api.styles import (
    DEFAULT_IP_ADAPTER_SCALE,
    DEFAULT_LORA_WEIGHT,
    PRODUCTION_STYLES,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "apps" / "web" / "e2e" / "fixtures" / "api-fixtures.json"
FIXTURE_MODULE = REPO_ROOT / "apps" / "web" / "e2e" / "fixtures" / "responses.ts"


def _load() -> dict:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def _extract(name: str) -> dict:
    data = _load()
    if name not in data:
        raise AssertionError(f"fixture {name} not found in {FIXTURES.name}")
    return data[name]


def test_the_fixture_file_exists():
    assert FIXTURES.is_file(), (
        "the E2E fixtures are missing; the mocked suite cannot be contract-checked"
    )


def test_the_typescript_module_reads_the_same_json_this_test_validates():
    """Otherwise this test could validate a file the browser suite never uses."""
    assert FIXTURE_MODULE.is_file()
    source = FIXTURE_MODULE.read_text(encoding="utf-8")
    assert "api-fixtures.json" in source, (
        "responses.ts must load api-fixtures.json, or the contract check above "
        "is validating a file the E2E suite does not actually serve"
    )


def test_every_fixture_in_the_json_is_reachable_from_the_typescript_module():
    """An unexported fixture is dead weight; an unvalidated one is a risk."""
    exported = FIXTURE_MODULE.read_text(encoding="utf-8")
    for name in _load():
        if name.startswith("_"):
            continue  # documentation blocks
        assert name in exported, f"{name} is defined in the JSON but not exported"


def test_the_styles_fixture_matches_the_real_response_model():
    StylesResponse.model_validate(_extract("STYLES_RESPONSE"))


@pytest.mark.parametrize("name", ["GENERATE_RESPONSE", "GENERATE_RESPONSE_PARTIAL_PASS"])
def test_the_generate_fixtures_match_the_real_response_model(name):
    GenerateResponse.model_validate(_extract(name))


@pytest.mark.parametrize("name", ["PROGRESS_SEQUENCE", "PROGRESS_COLD_LOAD"])
def test_every_progress_snapshot_matches_the_real_progress_model(name):
    snapshots = _extract(name)
    assert snapshots, f"{name} is empty"
    for snapshot in snapshots:
        GenerationProgressResponse.model_validate(snapshot)


def test_only_denoising_snapshots_carry_an_estimate():
    """The DR-013 rule, asserted in the fixtures the E2E suite serves.

    If a fixture published an estimate during model loading, the E2E test that
    proves the interface shows no percentage there would be testing the wrong
    thing - it would pass because the interface ignored data it should never
    have been given.
    """
    for name in ("PROGRESS_SEQUENCE", "PROGRESS_COLD_LOAD"):
        for snapshot in _extract(name):
            if snapshot["estimated_remaining_seconds"] is not None:
                assert snapshot["stage"] == "denoising", (
                    f"{name} publishes an estimate during {snapshot['stage']}, "
                    "which has no denominator to estimate from"
                )


def test_the_partial_pass_fixture_warns_the_way_the_service_does():
    """retro-poster returns its H4 limitation on every request, not sometimes."""
    fixture = _extract("GENERATE_RESPONSE_PARTIAL_PASS")
    retro = next(s for s in PRODUCTION_STYLES if s.key == "retro-poster")

    assert fixture["metadata"]["style_outcome"] == retro.outcome
    assert fixture["warnings"] == [retro.limitation]
    assert fixture["metadata"]["lora_sha256"] == retro.sha256


@pytest.mark.parametrize(
    "name",
    ["ERROR_BUSY", "ERROR_TIMEOUT", "ERROR_MODEL_UNAVAILABLE", "ERROR_VALIDATION_PROMPT"],
)
def test_the_error_fixtures_match_the_real_error_model(name):
    ErrorResponse.model_validate(_extract(name)["body"])


def test_the_idle_progress_fixture_matches_the_real_progress_model():
    GenerationProgressResponse.model_validate(_extract("PROGRESS_IDLE"))


def test_the_styles_fixture_agrees_with_the_production_styles():
    """Not just the shape - the actual three styles and their real outcomes."""
    fixture = _extract("STYLES_RESPONSE")
    keys = [style["key"] for style in fixture["styles"]]
    assert keys == [style.key for style in PRODUCTION_STYLES]

    for entry, style in zip(fixture["styles"], PRODUCTION_STYLES):
        assert entry["label"] == style.label
        assert entry["outcome"] == style.outcome
        assert entry["run_id"] == style.run_id
        assert entry["checkpoint_step"] == style.checkpoint_step
        assert entry["trigger"] == style.trigger

    assert fixture["default_lora_weight"] == DEFAULT_LORA_WEIGHT
    assert fixture["default_ip_adapter_scale"] == DEFAULT_IP_ADAPTER_SCALE


def test_the_generate_fixture_quotes_a_real_production_adapter():
    """A made-up hash would make the E2E metadata assertions meaningless."""
    metadata = _extract("GENERATE_RESPONSE")["metadata"]
    ukiyo = next(s for s in PRODUCTION_STYLES if s.key == "ukiyo-e")

    assert metadata["lora_sha256"] == ukiyo.sha256
    assert metadata["lora_run_id"] == ukiyo.run_id
    assert metadata["lora_checkpoint_step"] == ukiyo.checkpoint_step


def test_the_fixture_generation_id_is_one_the_service_would_actually_issue():
    from apps.api.generation import GENERATION_ID_PATTERN

    generate = _extract("GENERATE_RESPONSE")
    assert re.match(GENERATION_ID_PATTERN, generate["generation_id"]), (
        "the fixture id must satisfy the same pattern the endpoint enforces, "
        "otherwise the E2E suite tests a URL the real service would reject with 422"
    )


def test_the_extractor_is_sensitive():
    """A reader that silently returned {} would make every check above vacuous."""
    with pytest.raises(AssertionError, match="not found"):
        _extract("THIS_FIXTURE_DOES_NOT_EXIST")

    assert _extract("STYLES_RESPONSE")["styles"], "the extractor returned an empty result"


def test_the_generate_fixture_carries_no_filesystem_path():
    """The same rule the real metadata obeys must hold for the fixture."""
    raw = json.dumps(_extract("GENERATE_RESPONSE"))
    for forbidden in ("outputs/lora", ".safetensors", "C:\\\\", "/home/", "\\\\Users\\\\"):
        assert forbidden not in raw
