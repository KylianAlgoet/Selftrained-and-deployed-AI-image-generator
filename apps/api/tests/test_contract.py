"""Endpoint contract: shapes, status codes and what the response is allowed to say."""

from apps.api.styles import (
    DEFAULT_IP_ADAPTER_SCALE,
    DEFAULT_LORA_WEIGHT,
    PRODUCTION_STYLES,
)


def _generate(client, **overrides):
    data = {"prompt": "a coiled serpent", "style": "minimal-geometric", "seed": 42}
    data.update(overrides)
    return client.post("/api/generate", data=data)


def test_health_reports_pid_and_pipeline_state(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["pid"] > 0
    assert body["pipeline_loaded"] is False
    assert body["generation_in_progress"] is False
    assert body["single_worker_guard"] == "enforced"
    assert body["device_total_mb"] == 8187.5


def test_styles_lists_the_three_production_styles_with_their_outcomes(client):
    body = client.get("/api/styles").json()
    assert [s["key"] for s in body["styles"]] == [s.key for s in PRODUCTION_STYLES]
    assert body["default_lora_weight"] == DEFAULT_LORA_WEIGHT
    assert body["default_ip_adapter_scale"] == DEFAULT_IP_ADAPTER_SCALE
    assert (body["width"], body["height"]) == (512, 1536)

    by_key = {s["key"]: s for s in body["styles"]}
    assert by_key["retro-poster"]["outcome"] == "PARTIAL PASS"
    assert by_key["retro-poster"]["limitation"]
    assert by_key["minimal-geometric"]["outcome"] == "PASS"
    assert by_key["minimal-geometric"]["limitation"] == ""


def test_generate_returns_json_with_an_image_url_never_an_image_body(client):
    response = _generate(client)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    body = response.json()
    assert body["status"] == "completed"
    assert body["image_url"] == f"/api/generated/{body['generation_id']}"
    assert len(body["generation_id"]) == 22


def test_metadata_carries_the_reproducibility_fields(client):
    body = _generate(client).json()
    meta = body["metadata"]

    assert meta["base_model_revision"] == "451f4fe16113bff5a5d2269ed5ad43b0592e9a14"
    assert meta["lora_run_id"] == "EXP-027"
    assert meta["lora_checkpoint_step"] == 300
    assert meta["lora_weight"] == DEFAULT_LORA_WEIGHT
    assert meta["seed"] == 42
    assert meta["steps"] == 30
    assert meta["scheduler"] == "DPMSolverMultistepScheduler"
    assert (meta["width"], meta["height"]) == (512, 1536)
    assert meta["active_adapters"] == ["minimal-geometric"]
    assert meta["live_lora_modules"] == 128
    assert len(meta["lora_sha256"]) == 64
    assert len(meta["prompt_sha256"]) == 64


def test_metadata_never_exposes_a_filesystem_path(client):
    body = _generate(client).json()
    serialised = str(body)
    for leak in ("outputs/lora", "outputs\\lora", "C:\\", ".safetensors", "/home/"):
        assert leak not in serialised


def test_partial_pass_style_returns_its_limitation_as_a_warning(client):
    body = _generate(client, style="retro-poster").json()
    assert body["warnings"]
    assert "pseudo-text" in body["warnings"][0]


def test_full_pass_style_returns_no_warning(client):
    assert _generate(client, style="ukiyo-e").json()["warnings"] == []


def test_generated_image_is_served_for_a_known_id(client):
    body = _generate(client).json()
    response = client.get(body["image_url"])
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_prompt_is_built_in_the_scored_form(client, fake_pipeline):
    _generate(client, style="ukiyo-e", prompt="  a mountain and a rising sun  ")
    call = fake_pipeline.calls[-1]
    assert call["subject_prompt"] == "a mountain and a rising sun"
    assert call["style_key"] == "ukiyo-e"


def test_seed_defaults_when_omitted(client, fake_pipeline):
    client.post("/api/generate", data={"prompt": "a fox", "style": "ukiyo-e"})
    assert fake_pipeline.calls[-1]["seed"] == 42
