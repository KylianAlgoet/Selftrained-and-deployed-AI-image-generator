"""Read-only progress telemetry for the single in-flight generation.

WHAT THIS IS NOT. It is not a job queue, not a second execution path, and not a
way to control a generation. `POST /api/generate` remains synchronous and
authoritative: it is the request that returns the image, reports failure, and
owns the busy lock. This module only *observes*, so that a browser waiting on
that synchronous response can say something true about how far along it is.

Three rules make it safe to read while the GPU is working.

1. **Its own lock, and only its own.** The tracker never touches the generation
   busy lock. A progress read cannot start, stop, block or delay a generation;
   the worst it can do is return a snapshot a few milliseconds old.
2. **Nothing but numbers and strings.** No pipeline objects, tensors, images,
   uploaded bytes, filenames or paths ever enter this state. What cannot be
   stored cannot be leaked by the endpoint.
3. **Writes are bound to an operation id.** A reporter belongs to one
   generation. If a later generation has already begun, the older reporter's
   writes are dropped rather than corrupting the current operation's telemetry.

The honesty rule that shapes the numbers: **only denoising has a real
denominator.** Diffusers tells us "step 18 of 30", so a percentage there is a
measurement. Model loading, LoRA loading, VAE decoding and PNG encoding have no
progress signal at all, so this module publishes a *stage name* for them and
never a fabricated percentage. See `estimated_remaining_seconds`.
"""

import secrets
import threading
import time
from dataclasses import dataclass

# --- public vocabulary -------------------------------------------------------

STATUS_IDLE = "idle"
STATUS_GENERATING = "generating"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

STAGE_IDLE = "idle"
STAGE_PREPARING = "preparing"
STAGE_LOADING_MODEL = "loading-model"
STAGE_LOADING_STYLE = "loading-style"
STAGE_PREPARING_REFERENCE = "preparing-reference"
STAGE_DENOISING = "denoising"
STAGE_DECODING = "decoding"
STAGE_SAVING = "saving"
STAGE_COMPLETED = "completed"
STAGE_FAILED = "failed"

#: Every stage this service will ever publish. The frontend-owned
#: "applying-texture" state is deliberately absent: it happens in the browser
#: after the response arrives, and reporting it here would describe GPU work
#: that is already finished.
PUBLIC_STAGES = (
    STAGE_IDLE,
    STAGE_PREPARING,
    STAGE_LOADING_MODEL,
    STAGE_LOADING_STYLE,
    STAGE_PREPARING_REFERENCE,
    STAGE_DENOISING,
    STAGE_DECODING,
    STAGE_SAVING,
    STAGE_COMPLETED,
    STAGE_FAILED,
)

#: Completed step durations required before any remaining-time estimate is
#: published. The first denoising step of a request carries warm-up cost that is
#: not representative of the rest, so a single sample would produce a confident
#: and wrong number.
MIN_STEP_SAMPLES = 3

#: Weight of the newest sample in the exponential moving average of step
#: duration. High enough to follow a real slowdown, low enough that one hitching
#: step does not throw the estimate.
EMA_ALPHA = 0.3


@dataclass(frozen=True)
class ProgressSnapshot:
    """An immutable copy. Readers never see the tracker's own mutable state."""

    operation_id: str | None
    status: str
    stage: str
    current_step: int
    total_steps: int
    denoising_fraction: float
    elapsed_seconds: float
    estimated_remaining_seconds: float | None
    pipeline_loaded: bool = False

    def with_pipeline_loaded(self, loaded: bool) -> "ProgressSnapshot":
        """Pipeline residency is the pipeline's fact, not the tracker's."""
        return ProgressSnapshot(
            operation_id=self.operation_id,
            status=self.status,
            stage=self.stage,
            current_step=self.current_step,
            total_steps=self.total_steps,
            denoising_fraction=self.denoising_fraction,
            elapsed_seconds=self.elapsed_seconds,
            estimated_remaining_seconds=self.estimated_remaining_seconds,
            pipeline_loaded=bool(loaded),
        )


class ProgressReporter:
    """The write side, bound to one generation.

    Handed to the pipeline so it can report where it is. Every method is a
    no-op once a newer operation has started, which is what makes a slow or
    stray callback from an abandoned generation harmless.
    """

    def __init__(self, tracker: "ProgressTracker", operation_id: str) -> None:
        self._tracker = tracker
        self._operation_id = operation_id

    @property
    def operation_id(self) -> str:
        return self._operation_id

    def stage(self, stage: str) -> None:
        self._tracker._set_stage(self._operation_id, stage)

    def total_steps(self, total: int) -> None:
        self._tracker._set_total_steps(self._operation_id, total)

    def step(self, current_step: int) -> None:
        self._tracker._record_step(self._operation_id, current_step)

    def completed(self) -> None:
        self._tracker._finish(self._operation_id, STATUS_COMPLETED, STAGE_COMPLETED)

    def failed(self) -> None:
        self._tracker._finish(self._operation_id, STATUS_FAILED, STAGE_FAILED)


class NullReporter:
    """Used when no telemetry is wanted, so call sites need no `if progress`."""

    operation_id = ""

    def stage(self, stage: str) -> None:
        return None

    def total_steps(self, total: int) -> None:
        return None

    def step(self, current_step: int) -> None:
        return None

    def completed(self) -> None:
        return None

    def failed(self) -> None:
        return None


class ProgressTracker:
    """Process-local progress state for at most one active generation."""

    def __init__(self, clock=time.monotonic) -> None:
        # A monotonic clock: elapsed time must not jump if the system clock is
        # adjusted mid-generation, and a negative duration must be impossible.
        self._clock = clock
        self._lock = threading.Lock()
        self._reset_locked()

    # --- write side ----------------------------------------------------------

    def _reset_locked(self) -> None:
        self._operation_id: str | None = None
        self._status = STATUS_IDLE
        self._stage = STAGE_IDLE
        self._current_step = 0
        self._total_steps = 0
        self._started: float | None = None
        self._ended: float | None = None
        self._last_step_at: float | None = None
        self._samples = 0
        self._ema: float | None = None

    def begin(self) -> ProgressReporter:
        """Start a new operation, discarding the previous one's telemetry.

        The identifier is `secrets.token_urlsafe`: opaque, random, and carrying
        no relationship to the generation id, the output path or anything on
        disk. It exists so a client can tell one operation from another, and for
        nothing else.
        """
        operation_id = secrets.token_urlsafe(12)
        with self._lock:
            self._reset_locked()
            self._operation_id = operation_id
            self._status = STATUS_GENERATING
            self._stage = STAGE_PREPARING
            self._started = self._clock()
        return ProgressReporter(self, operation_id)

    def _is_current(self, operation_id: str) -> bool:
        return self._operation_id == operation_id and self._status == STATUS_GENERATING

    def _set_stage(self, operation_id: str, stage: str) -> None:
        with self._lock:
            if not self._is_current(operation_id):
                return
            self._stage = stage
            if stage == STAGE_DENOISING and self._last_step_at is None:
                self._last_step_at = self._clock()

    def _set_total_steps(self, operation_id: str, total: int) -> None:
        with self._lock:
            if not self._is_current(operation_id):
                return
            self._total_steps = max(0, int(total))

    def _record_step(self, operation_id: str, current_step: int) -> None:
        with self._lock:
            if not self._is_current(operation_id):
                return
            now = self._clock()
            step = max(0, int(current_step))
            # Only a forward move is a completed step. A repeated or out-of-order
            # index contributes no timing sample rather than a bogus duration.
            if step > self._current_step:
                if self._last_step_at is not None:
                    duration = now - self._last_step_at
                    if duration > 0:
                        self._samples += 1
                        self._ema = (
                            duration
                            if self._ema is None
                            else (EMA_ALPHA * duration) + ((1 - EMA_ALPHA) * self._ema)
                        )
                self._current_step = step
                self._last_step_at = now

    def _finish(self, operation_id: str, status: str, stage: str) -> None:
        with self._lock:
            if self._operation_id != operation_id:
                return
            self._status = status
            self._stage = stage
            if self._ended is None:
                self._ended = self._clock()

    # --- read side -----------------------------------------------------------

    def snapshot(self) -> ProgressSnapshot:
        """A cheap, immutable copy. Takes only this tracker's own lock."""
        with self._lock:
            if self._started is None:
                elapsed = 0.0
            else:
                end = self._ended if self._ended is not None else self._clock()
                elapsed = max(0.0, end - self._started)

            total = self._total_steps
            fraction = (self._current_step / total) if total > 0 else 0.0

            return ProgressSnapshot(
                operation_id=self._operation_id,
                status=self._status,
                stage=self._stage,
                current_step=self._current_step,
                total_steps=total,
                denoising_fraction=round(min(1.0, max(0.0, fraction)), 4),
                elapsed_seconds=round(elapsed, 2),
                estimated_remaining_seconds=self._estimate_locked(),
            )

    def _estimate_locked(self) -> float | None:
        """Remaining seconds, or None when no honest estimate exists.

        None is returned deliberately and often: before enough steps have been
        timed, outside denoising, and once the last step is done. Loading and
        decoding have no measurable progress, so any number attached to them
        would be invented. `None` is the correct answer, and the interface says
        so in words instead.
        """
        if self._status != STATUS_GENERATING or self._stage != STAGE_DENOISING:
            return None
        if self._ema is None or self._samples < MIN_STEP_SAMPLES:
            return None
        remaining_steps = self._total_steps - self._current_step
        if remaining_steps <= 0:
            return None
        return round(max(0.0, self._ema * remaining_steps), 2)


__all__ = [
    "EMA_ALPHA",
    "MIN_STEP_SAMPLES",
    "NullReporter",
    "PUBLIC_STAGES",
    "ProgressReporter",
    "ProgressSnapshot",
    "ProgressTracker",
    "STAGE_COMPLETED",
    "STAGE_DECODING",
    "STAGE_DENOISING",
    "STAGE_FAILED",
    "STAGE_IDLE",
    "STAGE_LOADING_MODEL",
    "STAGE_LOADING_STYLE",
    "STAGE_PREPARING",
    "STAGE_PREPARING_REFERENCE",
    "STAGE_SAVING",
    "STATUS_COMPLETED",
    "STATUS_FAILED",
    "STATUS_GENERATING",
    "STATUS_IDLE",
]
