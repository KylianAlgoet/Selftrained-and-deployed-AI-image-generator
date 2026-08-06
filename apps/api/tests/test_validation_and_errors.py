"""Every error path, and the promise that none of them leak internals."""

import pytest

from apps.api.generation import CheckpointUnavailable, PipelineUnavailable
from apps.api.pipeline import GenerationAborted


def _generate(client, **overrides):
    data = {"prompt": "a coiled serpent", "style": "minimal-geometric", "seed": 42}
    data.update(overrides)
    return client.post("/api/generate", data=data)


@pytest.mark.parametrize(
    "overrides, field",
    [
        ({"prompt": "   "}, "prompt"),
        ({"prompt": "x" * 401}, "prompt"),
        ({"style": "watercolour"}, "style"),
        ({"style": "retro-comic"}, "style"),  # the renamed style must stay rejected
        ({"lora_weight": 0.1}, "lora_weight"),
        ({"lora_weight": 1.5}, "lora_weight"),
        ({"ip_adapter_scale": 0.0}, "ip_adapter_scale"),
        ({"ip_adapter_scale": 0.95}, "ip_adapter_scale"),
    ],
)
def test_invalid_requests_are_422_with_the_offending_field(client, overrides, field):
    response = _generate(client, **overrides)
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_failed"
    assert body["field"] == field


def test_missing_checkpoint_is_503_and_says_nothing_about_paths(client, fake_pipeline):
    fake_pipeline.fail_with = CheckpointUnavailable(
        "minimal-geometric: adapter file missing at C:/secret/outputs/lora/x.safetensors"
    )
    response = _generate(client)
    assert response.status_code == 503
    body = response.json()
    assert body["error"] == "model_unavailable"
    assert "C:/secret" not in str(body)
    assert "safetensors" not in str(body)


def test_hash_mismatch_is_503(client, fake_pipeline):
    fake_pipeline.fail_with = CheckpointUnavailable("sha256 does not match the recorded value")
    assert _generate(client).status_code == 503


def test_pipeline_failure_is_503(client, fake_pipeline):
    fake_pipeline.fail_with = PipelineUnavailable("CUDA out of memory while loading")
    response = _generate(client)
    assert response.status_code == 503
    assert "CUDA" not in str(response.json())


def test_deadline_abort_is_504(client, fake_pipeline):
    fake_pipeline.fail_with = GenerationAborted(12, 30)
    response = _generate(client)
    assert response.status_code == 504
    assert response.json()["error"] == "generation_timeout"


def test_the_504_reports_how_far_the_generation_got(client, fake_pipeline):
    """The step counts make "it stopped early" checkable from the response.

    Wall-clock time cannot show it: a cold first request spends most of its
    duration loading the model rather than denoising.
    """
    fake_pipeline.fail_with = GenerationAborted(14, 30)
    detail = _generate(client).json()["detail"]
    assert "14" in detail and "30" in detail


def test_the_abort_carries_its_step_counts():
    error = GenerationAborted(8, 30)
    assert error.steps_run == 8
    assert error.steps_total == 30
    assert "8 of 30" in str(error)


def test_unexpected_failure_is_500_with_a_safe_message(client, fake_pipeline):
    fake_pipeline.fail_with = RuntimeError("assert failed at /srv/app/pipeline.py:214")
    response = _generate(client)
    assert response.status_code == 500
    body = response.json()
    assert body["error"] == "generation_failed"
    assert "pipeline.py" not in str(body)
    assert "/srv/" not in str(body)


@pytest.mark.parametrize(
    "generation_id",
    [
        "../../../../etc/passwd",
        "..%2f..%2fsecret",
        "short",
        "with space and punctuation!!",
        "a" * 64,
    ],
)
def test_malformed_generation_ids_are_rejected(client, generation_id):
    response = client.get(f"/api/generated/{generation_id}")
    assert response.status_code in (404, 422)
    assert response.headers["content-type"].startswith("application/json")


def test_unknown_but_wellformed_generation_id_is_404(client):
    response = client.get("/api/generated/" + "A" * 22)
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_a_generation_id_is_a_registry_key_not_a_path(service, tmp_path):
    """The id never reaches the filesystem, so traversal has nothing to traverse."""
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"\x89PNG not yours")
    assert service.resolve("../outside") is None
    assert service.resolve(str(outside)) is None
