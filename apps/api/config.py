"""Service configuration, read from the environment described by `.env.example`.

Deliberately free of torch, diffusers and FastAPI imports so the settings and the
single-process guard can be unit-tested without a GPU and without an app.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The deck format, fixed by DR-007. Generation happens at this geometry directly;
# the square-crop alternative was rejected in Prototype 1.
GENERATION_WIDTH = 512
GENERATION_HEIGHT = 1536

# Generated PNGs are derived artifacts and live in the git-ignored outputs tree,
# next to every other generated image in this project.
GENERATED_SUBDIR = Path("outputs") / "api"


class ConfigurationError(RuntimeError):
    """Raised when the environment asks for something this service cannot serve."""


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8000
    allowed_origins: tuple[str, ...] = ("http://localhost:5173",)
    max_upload_size_mb: int = 10
    generation_timeout_seconds: float = 120.0
    default_seed: int = 42
    generated_dir: Path = field(default_factory=lambda: REPO_ROOT / GENERATED_SUBDIR)
    # How many finished generations stay resolvable. The registry is in-memory and
    # the service is single-process, so this only bounds one process's own history.
    max_retained_generations: int = 64

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


def _split_origins(raw: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def assert_single_worker(env: dict[str, str] | None = None) -> None:
    """Reject a multi-worker configuration before the pipeline is ever built.

    WHY THIS EXISTS, and why it rejects rather than warns.

    The busy lock in `generation.py` is a `threading.Lock`: it is PROCESS-LOCAL.
    Two Uvicorn workers would each hold their own lock, their own resident
    pipeline and their own in-flight generation, and would then compete for one
    8 GB device. That is not a throughput question - EXP-019b/EXP-032 measured the
    production stack at 7985.5 MiB of 8187.5 MiB physical, so a SECOND resident
    pipeline does not fit at all. The first symptom would be an OOM in whichever
    request happened to be running, which is an awful way to discover a
    configuration mistake.

    What this can and cannot detect: it reads the worker-count environment
    variables a process can actually see. It CANNOT detect a second API process
    someone started by hand in another terminal - nothing inside one process can.
    Two separately launched API processes are UNSUPPORTED, and `/api/health`
    reports the PID so a duplicate is at least visible.
    """
    env = os.environ if env is None else env
    for name in ("WEB_CONCURRENCY", "UVICORN_WORKERS", "GUNICORN_WORKERS"):
        raw = (env.get(name) or "").strip()
        if not raw:
            continue
        try:
            workers = int(raw)
        except ValueError as err:
            raise ConfigurationError(
                f"{name}={raw!r} is not an integer; this service supports exactly one worker"
            ) from err
        if workers > 1:
            raise ConfigurationError(
                f"{name}={workers} but DeckForge AI supports exactly one API worker. "
                "The GPU holds one resident pipeline with about 202 MiB spare, so a second "
                "worker cannot fit and the single-flight lock would not span it. "
                "Start with: python -m uvicorn apps.api.main:app --workers 1"
            )


def load_settings(env: dict[str, str] | None = None) -> Settings:
    env = os.environ if env is None else env
    assert_single_worker(env)

    generated = env.get("GENERATED_OUTPUT_DIR")
    return Settings(
        host=env.get("API_HOST", "127.0.0.1"),
        port=int(env.get("API_PORT", "8000")),
        allowed_origins=_split_origins(env.get("ALLOWED_ORIGINS", "http://localhost:5173")),
        max_upload_size_mb=int(env.get("MAX_UPLOAD_SIZE_MB", "10")),
        generation_timeout_seconds=float(env.get("GENERATION_TIMEOUT_SECONDS", "120")),
        default_seed=int(env.get("DEFAULT_SEED", "42")),
        generated_dir=Path(generated) if generated else REPO_ROOT / GENERATED_SUBDIR,
    )
