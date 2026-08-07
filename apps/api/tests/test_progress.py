"""Progress telemetry: honest numbers, no leakage, and no influence on the GPU.

NO GPU, NO MODEL, NO NETWORK. The tracker is exercised directly with an injected
clock, and the endpoint against the fake pipeline, so every timing assertion here
is deterministic rather than a race with a real generation.

Three questions these tests exist to answer, because getting any of them wrong
would be worse than having no progress bar at all:

1. Does reading progress interfere with the generation? (It must not touch the
   busy lock, in either direction.)
2. Is the reported progress real? (Steps come from the loop; an estimate appears
   only once steps have actually been timed.)
3. Does the composed callback still abort on the deadline? (Progress reporting
   must not have replaced the thing that makes a 504 truthful.)
"""

import threading

import pytest

from apps.api.pipeline import compose_step_callbacks
from apps.api.progress import (
    MIN_STEP_SAMPLES,
    PUBLIC_STAGES,
    STAGE_DENOISING,
    STAGE_IDLE,
    STAGE_PREPARING,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_GENERATING,
    STATUS_IDLE,
    NullReporter,
    ProgressTracker,
)


class FakeClock:
    """A monotonic clock the test advances by hand."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def tracker(clock) -> ProgressTracker:
    return ProgressTracker(clock=clock)


# --- the tracker -------------------------------------------------------------


def test_a_fresh_tracker_is_idle_and_claims_no_operation(tracker):
    snapshot = tracker.snapshot()
    assert snapshot.status == STATUS_IDLE
    assert snapshot.stage == STAGE_IDLE
    assert snapshot.operation_id is None
    assert snapshot.current_step == 0
    assert snapshot.total_steps == 0
    assert snapshot.elapsed_seconds == 0.0
    assert snapshot.estimated_remaining_seconds is None


def test_begin_starts_one_operation_in_the_preparing_stage(tracker):
    reporter = tracker.begin()
    snapshot = tracker.snapshot()
    assert snapshot.status == STATUS_GENERATING
    assert snapshot.stage == STAGE_PREPARING
    assert snapshot.operation_id == reporter.operation_id


def test_operation_ids_are_opaque_and_unique(tracker):
    seen = {tracker.begin().operation_id for _ in range(50)}
    assert len(seen) == 50
    for operation_id in seen:
        # Opaque: no path separators, no extension, no embedded generation id.
        assert "/" not in operation_id and "\\" not in operation_id
        assert "." not in operation_id
        assert len(operation_id) >= 16


def test_steps_and_stages_are_reported_verbatim(tracker):
    reporter = tracker.begin()
    reporter.total_steps(30)
    reporter.stage(STAGE_DENOISING)
    reporter.step(18)

    snapshot = tracker.snapshot()
    assert snapshot.stage == STAGE_DENOISING
    assert snapshot.current_step == 18
    assert snapshot.total_steps == 30
    assert snapshot.denoising_fraction == pytest.approx(0.6)


def test_every_published_stage_is_in_the_declared_vocabulary(tracker):
    reporter = tracker.begin()
    for stage in PUBLIC_STAGES:
        reporter.stage(stage)
        assert tracker.snapshot().stage == stage
    # The frontend-owned state is not a backend stage and never becomes one.
    assert "applying-texture" not in PUBLIC_STAGES


def test_elapsed_time_uses_the_monotonic_clock(tracker, clock):
    tracker.begin()
    clock.advance(8.4)
    assert tracker.snapshot().elapsed_seconds == pytest.approx(8.4)


def test_elapsed_time_freezes_when_the_operation_ends(tracker, clock):
    reporter = tracker.begin()
    clock.advance(12.0)
    reporter.completed()
    clock.advance(60.0)
    assert tracker.snapshot().elapsed_seconds == pytest.approx(12.0)


# --- the estimate ------------------------------------------------------------


def test_no_estimate_before_enough_real_steps_have_been_timed(tracker, clock):
    reporter = tracker.begin()
    reporter.total_steps(30)
    reporter.stage(STAGE_DENOISING)

    for step in range(1, MIN_STEP_SAMPLES):
        clock.advance(0.4)
        reporter.step(step)
        assert tracker.snapshot().estimated_remaining_seconds is None


def test_an_estimate_appears_once_steps_are_measured(tracker, clock):
    reporter = tracker.begin()
    reporter.total_steps(30)
    reporter.stage(STAGE_DENOISING)
    for step in range(1, 11):
        clock.advance(0.4)
        reporter.step(step)

    estimate = tracker.snapshot().estimated_remaining_seconds
    # 20 steps left at a measured 0.4 s each. The EMA is seeded from real
    # samples, so this is arithmetic on observations, not a guess.
    assert estimate == pytest.approx(8.0, abs=0.05)


def test_no_estimate_outside_denoising(tracker, clock):
    reporter = tracker.begin()
    reporter.total_steps(30)
    reporter.stage(STAGE_DENOISING)
    for step in range(1, 11):
        clock.advance(0.4)
        reporter.step(step)
    assert tracker.snapshot().estimated_remaining_seconds is not None

    # Decoding has no measurable progress, so no number is offered for it.
    reporter.stage("decoding")
    assert tracker.snapshot().estimated_remaining_seconds is None


def test_no_estimate_once_the_last_step_is_done(tracker, clock):
    reporter = tracker.begin()
    reporter.total_steps(30)
    reporter.stage(STAGE_DENOISING)
    for step in range(1, 31):
        clock.advance(0.4)
        reporter.step(step)
    assert tracker.snapshot().estimated_remaining_seconds is None


def test_the_estimate_is_never_negative_and_the_fraction_never_exceeds_one(tracker, clock):
    reporter = tracker.begin()
    reporter.total_steps(30)
    reporter.stage(STAGE_DENOISING)
    for step in range(1, 41):  # more callbacks than declared steps
        clock.advance(0.4)
        reporter.step(step)

    snapshot = tracker.snapshot()
    assert snapshot.denoising_fraction <= 1.0
    assert snapshot.estimated_remaining_seconds is None


def test_a_zero_total_never_divides_by_zero(tracker):
    reporter = tracker.begin()
    reporter.stage(STAGE_DENOISING)
    reporter.step(5)
    assert tracker.snapshot().denoising_fraction == 0.0


def test_a_repeated_step_index_contributes_no_timing_sample(tracker, clock):
    reporter = tracker.begin()
    reporter.total_steps(30)
    reporter.stage(STAGE_DENOISING)
    for step in range(1, 11):
        clock.advance(0.4)
        reporter.step(step)
    before = tracker.snapshot()

    clock.advance(30.0)
    reporter.step(10)  # same index again: not a completed step
    after = tracker.snapshot()

    assert after.current_step == before.current_step
    assert after.estimated_remaining_seconds == pytest.approx(
        before.estimated_remaining_seconds, abs=0.01
    )


# --- lifecycle and stale state ----------------------------------------------


def test_completion_and_failure_are_distinguishable(tracker):
    tracker.begin().completed()
    assert tracker.snapshot().status == STATUS_COMPLETED
    tracker.begin().failed()
    assert tracker.snapshot().status == STATUS_FAILED


def test_a_new_operation_resets_the_previous_one(tracker, clock):
    first = tracker.begin()
    first.total_steps(30)
    first.stage(STAGE_DENOISING)
    first.step(29)
    first.completed()

    second = tracker.begin()
    snapshot = tracker.snapshot()
    assert snapshot.operation_id == second.operation_id
    assert snapshot.operation_id != first.operation_id
    assert snapshot.status == STATUS_GENERATING
    assert snapshot.stage == STAGE_PREPARING
    assert snapshot.current_step == 0
    assert snapshot.total_steps == 0
    assert snapshot.estimated_remaining_seconds is None


def test_a_stale_reporter_cannot_write_over_the_current_operation(tracker):
    stale = tracker.begin()
    current = tracker.begin()
    current.total_steps(30)
    current.stage(STAGE_DENOISING)
    current.step(4)

    stale.step(29)
    stale.stage("saving")
    stale.total_steps(999)
    stale.completed()

    snapshot = tracker.snapshot()
    assert snapshot.operation_id == current.operation_id
    assert snapshot.current_step == 4
    assert snapshot.total_steps == 30
    assert snapshot.stage == STAGE_DENOISING
    assert snapshot.status == STATUS_GENERATING


def test_writes_after_completion_are_ignored(tracker):
    reporter = tracker.begin()
    reporter.completed()
    reporter.step(29)
    reporter.stage(STAGE_DENOISING)

    snapshot = tracker.snapshot()
    assert snapshot.status == STATUS_COMPLETED
    assert snapshot.current_step == 0


def test_snapshots_are_immutable_copies(tracker):
    reporter = tracker.begin()
    reporter.total_steps(30)
    reporter.stage(STAGE_DENOISING)
    reporter.step(3)
    snapshot = tracker.snapshot()

    reporter.step(9)

    # The copy taken earlier did not move under the reader's feet.
    assert snapshot.current_step == 3
    assert tracker.snapshot().current_step == 9
    with pytest.raises(Exception):
        snapshot.current_step = 99  # frozen dataclass


def test_concurrent_readers_and_a_writer_never_see_a_torn_snapshot(tracker):
    reporter = tracker.begin()
    reporter.total_steps(30)
    reporter.stage(STAGE_DENOISING)
    seen: list[tuple[int, int]] = []
    stop = threading.Event()

    def read() -> None:
        while not stop.is_set():
            snap = tracker.snapshot()
            seen.append((snap.current_step, snap.total_steps))

    readers = [threading.Thread(target=read) for _ in range(4)]
    for thread in readers:
        thread.start()
    for step in range(1, 31):
        reporter.step(step)
    stop.set()
    for thread in readers:
        thread.join(timeout=5)

    assert seen, "the readers never ran"
    for current, total in seen:
        assert total == 30
        assert 0 <= current <= 30


def test_the_null_reporter_accepts_every_call_and_does_nothing():
    reporter = NullReporter()
    reporter.stage(STAGE_DENOISING)
    reporter.total_steps(30)
    reporter.step(1)
    reporter.completed()
    reporter.failed()


# --- callback composition ----------------------------------------------------


def test_composition_runs_every_callback_and_returns_the_kwargs():
    order: list[str] = []
    marker = {"latents": "untouched"}

    def first(pipe, index, timestep, kwargs):
        order.append("first")
        return kwargs

    def second(pipe, index, timestep, kwargs):
        order.append("second")
        return kwargs

    composed = compose_step_callbacks(first, second)
    returned = composed(object(), 0, 1, marker)

    assert order == ["first", "second"]
    assert returned is marker


def test_composition_survives_a_callback_that_returns_nothing():
    marker = {"latents": "untouched"}

    def silent(pipe, index, timestep, kwargs):
        return None

    def echo(pipe, index, timestep, kwargs):
        return kwargs

    composed = compose_step_callbacks(silent, echo)
    assert composed(object(), 0, 1, marker) is marker


def test_the_deadline_still_interrupts_when_progress_is_also_reported(tracker):
    """The regression this file exists for.

    Passing a progress callback as `callback_on_step_end` would have REPLACED the
    deadline callback - diffusers accepts only one - and the generation would
    have quietly become uninterruptible while looking instrumented.
    """

    class FakePipe:
        _interrupt = False

    pipe = FakePipe()
    reporter = tracker.begin()
    reporter.total_steps(30)
    reporter.stage(STAGE_DENOISING)

    def deadline_callback(inner_pipe, step_index, timestep, kwargs):
        if step_index + 1 >= 14:
            inner_pipe._interrupt = True
        return kwargs

    def progress_callback(inner_pipe, step_index, timestep, kwargs):
        reporter.step(step_index + 1)
        return kwargs

    composed = compose_step_callbacks(deadline_callback, progress_callback)
    kwargs = {"latents": "untouched"}
    for index in range(14):
        kwargs = composed(pipe, index, 1, kwargs)

    assert pipe._interrupt is True, "the deadline callback stopped running"
    assert tracker.snapshot().current_step == 14, "progress was not recorded"
    assert kwargs == {"latents": "untouched"}, "a callback mutated the loop kwargs"


# --- the endpoint ------------------------------------------------------------


def test_progress_is_idle_before_anything_has_run(client):
    body = client.get("/api/generation-progress").json()
    assert body["status"] == STATUS_IDLE
    assert body["stage"] == STAGE_IDLE
    assert body["operation_id"] is None
    assert body["pipeline_loaded"] is False
    assert body["estimated_remaining_seconds"] is None


def test_progress_reports_a_completed_generation(client, style_keys):
    response = client.post(
        "/api/generate", data={"prompt": "a mountain", "style": style_keys[0]}
    )
    assert response.status_code == 200

    body = client.get("/api/generation-progress").json()
    assert body["status"] == STATUS_COMPLETED
    assert body["operation_id"]
    assert body["pipeline_loaded"] is True


def test_progress_reports_a_failed_generation(client, fake_pipeline, style_keys):
    from apps.api.pipeline import PipelineUnavailable

    fake_pipeline.fail_with = PipelineUnavailable("boom")
    response = client.post(
        "/api/generate", data={"prompt": "a mountain", "style": style_keys[0]}
    )
    assert response.status_code == 503

    body = client.get("/api/generation-progress").json()
    assert body["status"] == STATUS_FAILED
    assert body["stage"] == "failed"
    # The failure reason belongs in the server log and the POST response,
    # never in telemetry a browser polls.
    assert "boom" not in str(body)


def test_a_deadline_abort_is_reported_as_failed(client, fake_pipeline, style_keys):
    from apps.api.pipeline import GenerationAborted

    fake_pipeline.fail_with = GenerationAborted(14, 30)
    assert (
        client.post(
            "/api/generate", data={"prompt": "a mountain", "style": style_keys[0]}
        ).status_code
        == 504
    )
    assert client.get("/api/generation-progress").json()["status"] == STATUS_FAILED


def test_each_generation_gets_a_fresh_operation_id(client, style_keys):
    seen = []
    for _ in range(3):
        client.post("/api/generate", data={"prompt": "a mountain", "style": style_keys[0]})
        seen.append(client.get("/api/generation-progress").json()["operation_id"])
    assert len(set(seen)) == 3


def test_progress_during_an_active_generation_reports_real_step_values(
    client, fake_pipeline, service, style_keys
):
    """The endpoint is polled WHILE a generation holds the lock."""
    from apps.api.tests.conftest import Gate

    gate = Gate()
    fake_pipeline.before_generate = gate

    result: dict = {}

    def run() -> None:
        result["response"] = client.post(
            "/api/generate", data={"prompt": "a mountain", "style": style_keys[0]}
        )

    worker = threading.Thread(target=run)
    worker.start()
    try:
        assert gate.entered.wait(timeout=10)
        assert service.busy is True

        reporter = fake_pipeline.last_reporter
        assert reporter is not None, "the service did not hand a reporter to the pipeline"
        reporter.total_steps(30)
        reporter.stage(STAGE_DENOISING)
        reporter.step(18)

        body = client.get("/api/generation-progress").json()
        assert body["status"] == STATUS_GENERATING
        assert body["stage"] == STAGE_DENOISING
        assert body["current_step"] == 18
        assert body["total_steps"] == 30
        assert body["denoising_fraction"] == pytest.approx(0.6)

        # Reading progress neither took nor released the generation lock.
        assert service.busy is True
        for _ in range(5):
            client.get("/api/generation-progress")
        assert service.busy is True
    finally:
        gate.release.set()
        worker.join(timeout=10)

    assert result["response"].status_code == 200
    assert service.busy is False


def test_polling_progress_does_not_make_a_second_request_possible(
    client, fake_pipeline, service, style_keys
):
    """A poll must not release the lock and let a concurrent generation in."""
    from apps.api.tests.conftest import Gate

    gate = Gate()
    fake_pipeline.before_generate = gate
    worker = threading.Thread(
        target=lambda: client.post(
            "/api/generate", data={"prompt": "a mountain", "style": style_keys[0]}
        )
    )
    worker.start()
    try:
        assert gate.entered.wait(timeout=10)
        for _ in range(10):
            assert client.get("/api/generation-progress").status_code == 200
        second = client.post(
            "/api/generate", data={"prompt": "another", "style": style_keys[0]}
        )
        assert second.status_code == 409
        assert second.json()["error"] == "generation_in_progress"
    finally:
        gate.release.set()
        worker.join(timeout=10)


def test_a_refused_request_does_not_reset_the_running_operation(
    client, fake_pipeline, service, style_keys
):
    from apps.api.tests.conftest import Gate

    gate = Gate()
    fake_pipeline.before_generate = gate
    worker = threading.Thread(
        target=lambda: client.post(
            "/api/generate", data={"prompt": "a mountain", "style": style_keys[0]}
        )
    )
    worker.start()
    try:
        assert gate.entered.wait(timeout=10)
        reporter = fake_pipeline.last_reporter
        reporter.total_steps(30)
        reporter.stage(STAGE_DENOISING)
        reporter.step(12)
        before = client.get("/api/generation-progress").json()

        client.post("/api/generate", data={"prompt": "another", "style": style_keys[0]})

        after = client.get("/api/generation-progress").json()
        assert after["operation_id"] == before["operation_id"]
        assert after["current_step"] == 12
    finally:
        gate.release.set()
        worker.join(timeout=10)


def test_progress_never_exposes_paths_filenames_or_prompts(
    client, fake_pipeline, style_keys, png_bytes
):
    response = client.post(
        "/api/generate",
        data={"prompt": "a secret mountain phrase", "style": style_keys[0]},
        files={"reference_image": ("my-private-photo.png", png_bytes, "image/png")},
    )
    assert response.status_code == 200

    raw = client.get("/api/generation-progress").text
    body = client.get("/api/generation-progress").json()

    assert "my-private-photo" not in raw
    assert "secret mountain phrase" not in raw
    assert "safetensors" not in raw
    assert "Expert Lab" not in raw
    assert "outputs" not in raw
    assert "\\\\" not in raw and "/home" not in raw
    assert ".png" not in raw
    # And positively: the payload is exactly the declared telemetry fields.
    assert set(body) == {
        "operation_id",
        "status",
        "stage",
        "current_step",
        "total_steps",
        "denoising_fraction",
        "elapsed_seconds",
        "estimated_remaining_seconds",
        "pipeline_loaded",
    }


def test_progress_carries_no_style_lora_or_reference_state(client, style_keys, png_bytes):
    client.post(
        "/api/generate",
        data={"prompt": "a mountain", "style": style_keys[0], "lora_weight": "0.7"},
        files={"reference_image": ("ref.png", png_bytes, "image/png")},
    )
    raw = client.get("/api/generation-progress").text
    for leaked in style_keys:
        assert leaked not in raw
    assert "lora" not in raw.lower()
    assert "adapter" not in raw.lower()
    assert "sha256" not in raw.lower()


def test_the_generate_contract_is_unchanged_by_progress(client, style_keys):
    """The progress work must not have altered what POST /api/generate returns."""
    response = client.post(
        "/api/generate", data={"prompt": "a mountain", "style": style_keys[0]}
    )
    body = response.json()
    assert set(body) == {"generation_id", "status", "image_url", "metadata", "warnings"}
    assert "operation_id" not in body
    assert "progress" not in body
    assert body["status"] == "completed"
