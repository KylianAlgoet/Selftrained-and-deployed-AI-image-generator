"""The busy lock, the single-process invariant, and the LoRA lifecycle.

These are the tests protecting the two properties that make the service safe on
one 8 GB device: only one generation ever touches the GPU, and exactly one style
adapter is ever live.
"""

import threading

import pytest

from apps.api.config import ConfigurationError, Settings, assert_single_worker
from apps.api.generation import GenerationBusy, GenerationService
from apps.api.pipeline import GenerationAborted

from .conftest import Gate


def _generate(client, **overrides):
    data = {"prompt": "a coiled serpent", "style": "minimal-geometric", "seed": 42}
    data.update(overrides)
    return client.post("/api/generate", data=data)


# --- single-process invariant ------------------------------------------------


@pytest.mark.parametrize("name", ["WEB_CONCURRENCY", "UVICORN_WORKERS", "GUNICORN_WORKERS"])
def test_more_than_one_worker_is_rejected(name):
    with pytest.raises(ConfigurationError) as err:
        assert_single_worker({name: "2"})
    assert "one API worker" in str(err.value)


@pytest.mark.parametrize("name", ["WEB_CONCURRENCY", "UVICORN_WORKERS"])
def test_exactly_one_worker_is_accepted(name):
    assert_single_worker({name: "1"})


def test_a_nonnumeric_worker_count_is_rejected_rather_than_ignored():
    with pytest.raises(ConfigurationError):
        assert_single_worker({"WEB_CONCURRENCY": "auto"})


def test_absent_worker_settings_are_fine():
    assert_single_worker({})


def test_health_exposes_the_pid_so_a_duplicate_process_is_visible(client):
    import os

    assert client.get("/api/health").json()["pid"] == os.getpid()


# --- the busy lock -----------------------------------------------------------


def test_a_second_request_during_generation_is_409(client, fake_pipeline):
    gate = Gate()
    fake_pipeline.before_generate = gate

    first: dict = {}

    def run_first():
        first["response"] = _generate(client)

    thread = threading.Thread(target=run_first)
    thread.start()
    assert gate.entered.wait(timeout=10), "first generation never started"

    busy = _generate(client)
    assert busy.status_code == 409
    assert busy.json()["error"] == "generation_in_progress"

    gate.release.set()
    thread.join(timeout=10)
    assert first["response"].status_code == 200


def test_health_reports_generation_in_progress_while_locked(client, fake_pipeline):
    gate = Gate()
    fake_pipeline.before_generate = gate

    thread = threading.Thread(target=lambda: _generate(client))
    thread.start()
    assert gate.entered.wait(timeout=10)

    assert client.get("/api/health").json()["generation_in_progress"] is True

    gate.release.set()
    thread.join(timeout=10)
    assert client.get("/api/health").json()["generation_in_progress"] is False


def test_the_lock_is_released_only_after_the_generation_call_returns(service, fake_pipeline):
    """The release happens in `finally`, downstream of the work - never before it."""
    observed: list[bool] = []

    def observe():
        # Inside the generation call the lock must still be held.
        observed.append(service.busy)

    fake_pipeline.before_generate = observe
    service.generate(
        style_key="ukiyo-e",
        subject_prompt="a fox",
        seed=42,
        lora_weight=0.7,
        ip_adapter_scale=0.55,
    )
    assert observed == [True]
    assert service.busy is False


def test_an_aborted_generation_releases_the_lock_after_cleanup(service, fake_pipeline):
    fake_pipeline.fail_with = GenerationAborted(12, 30)
    with pytest.raises(GenerationAborted):
        service.generate(
            style_key="ukiyo-e",
            subject_prompt="a fox",
            seed=42,
            lora_weight=0.7,
            ip_adapter_scale=0.55,
        )
    assert service.busy is False


def test_a_later_request_succeeds_after_a_controlled_abort(client, fake_pipeline):
    fake_pipeline.fail_with = GenerationAborted(12, 30)
    assert _generate(client).status_code == 504
    assert _generate(client).status_code == 200


def test_a_later_request_succeeds_after_an_unexpected_failure(client, fake_pipeline):
    fake_pipeline.fail_with = RuntimeError("boom")
    assert _generate(client).status_code == 500
    assert _generate(client).status_code == 200


def test_the_lock_is_not_released_by_a_client_disconnect(service, fake_pipeline):
    """No background thread exists, so nothing can outlive the request.

    The service holds the lock for the duration of a synchronous call. There is no
    code path that returns to the caller while `pipeline.generate` is still
    running, which is exactly why a disconnected client cannot free the GPU.
    """
    gate = Gate()
    fake_pipeline.before_generate = gate
    errors: list[Exception] = []

    def run():
        try:
            service.generate(
                style_key="ukiyo-e",
                subject_prompt="a fox",
                seed=42,
                lora_weight=0.7,
                ip_adapter_scale=0.55,
            )
        except Exception as err:  # pragma: no cover - failure would fail the test
            errors.append(err)

    thread = threading.Thread(target=run)
    thread.start()
    assert gate.entered.wait(timeout=10)

    # The "client" is gone; the server still refuses new work.
    assert service.busy is True
    with pytest.raises(GenerationBusy):
        service.generate(
            style_key="ukiyo-e",
            subject_prompt="another",
            seed=1,
            lora_weight=0.7,
            ip_adapter_scale=0.55,
        )

    gate.release.set()
    thread.join(timeout=10)
    assert not errors
    assert service.busy is False


# --- LoRA lifecycle ----------------------------------------------------------


def test_style_switching_keeps_exactly_one_adapter_live(client, fake_pipeline):
    for style in ("minimal-geometric", "ukiyo-e", "retro-poster", "minimal-geometric"):
        body = _generate(client, style=style).json()
        assert body["metadata"]["active_adapters"] == [style]
        assert fake_pipeline.loaded_adapters == (style,)

    assert fake_pipeline.switch_log == [
        "minimal-geometric",
        "ukiyo-e",
        "retro-poster",
        "minimal-geometric",
    ]


def test_a_style_switch_after_a_failed_generation_is_clean(client, fake_pipeline):
    fake_pipeline.fail_with = RuntimeError("boom")
    assert _generate(client, style="ukiyo-e").status_code == 500

    body = _generate(client, style="retro-poster").json()
    assert body["metadata"]["active_adapters"] == ["retro-poster"]
    assert fake_pipeline.loaded_adapters == ("retro-poster",)


def test_reference_then_no_reference_then_reference_leaves_no_stale_state(
    client, fake_pipeline, png_bytes
):
    """A prompt-only request in between must not inherit the earlier reference."""
    with_ref = client.post(
        "/api/generate",
        data={"prompt": "a fox", "style": "ukiyo-e", "ip_adapter_scale": 0.55},
        files={"reference_image": ("ref.png", png_bytes, "image/png")},
    ).json()
    assert with_ref["metadata"]["reference_present"] is True
    assert with_ref["metadata"]["ip_adapter_scale"] == 0.55

    without = _generate(client, style="ukiyo-e").json()
    assert without["metadata"]["reference_present"] is False
    # Scale 0.0 is the neutralised state; a leaked reference would show as 0.55.
    assert without["metadata"]["ip_adapter_scale"] == 0.0
    assert fake_pipeline.calls[-1]["reference_image"] is None

    again = client.post(
        "/api/generate",
        data={"prompt": "a fox", "style": "ukiyo-e", "ip_adapter_scale": 0.6},
        files={"reference_image": ("ref.png", png_bytes, "image/png")},
    ).json()
    assert again["metadata"]["reference_present"] is True
    assert again["metadata"]["ip_adapter_scale"] == 0.6

    assert fake_pipeline.scale_history == [0.55, 0.0, 0.6]


# --- retention ---------------------------------------------------------------


def test_old_generations_are_evicted_and_their_files_removed(tmp_path, fake_pipeline):
    settings = Settings(generated_dir=tmp_path / "generated", max_retained_generations=2)
    service = GenerationService(settings, pipeline=fake_pipeline)

    ids = []
    for index in range(4):
        metadata, _ = service.generate(
            style_key="ukiyo-e",
            subject_prompt=f"subject {index}",
            seed=index,
            lora_weight=0.7,
            ip_adapter_scale=0.55,
        )
        ids.append(metadata.generation_id)

    assert service.resolve(ids[0]) is None
    assert service.resolve(ids[1]) is None
    assert service.resolve(ids[2]) is not None
    assert service.resolve(ids[3]) is not None
    assert len(list((tmp_path / "generated").iterdir())) == 2
