"""Test fixtures for the API layer.

NO GPU, NO MODEL, NO NETWORK. The resident pipeline is replaced by a fake that
records what it was asked to do, so these tests exercise the HTTP contract, the
upload rules, the busy lock and the adapter lifecycle without loading 5 GB of
weights. The real pipeline is exercised on the GPU in EXP-034 and the Phase-D
validation matrix, and those results are recorded as evidence rather than
simulated here.
"""

import io
import threading

import pytest
from PIL import Image

from apps.api.config import Settings
from apps.api.generation import GenerationService
from apps.api.pipeline import GenerationOutcome
from apps.api.styles import PRODUCTION_STYLES, production_style


class FakePipeline:
    """Stands in for `ResidentPipeline` with the same surface the service uses."""

    def __init__(self) -> None:
        self.loaded = False
        self.active_style = None
        self.calls: list[dict] = []
        self.switch_log: list[str] = []
        # Mirrors the real invariant: at most one adapter name is ever live.
        self.loaded_adapters: tuple[str, ...] = ()
        self.fail_with: Exception | None = None
        self.before_generate = None
        self.scale_history: list[float] = []

    def device_report(self) -> dict:
        import os

        return {
            "pid": os.getpid(),
            "pipeline_loaded": self.loaded,
            "active_style": self.active_style,
            "device_total_mb": 8187.5,
            "cuda_available": False,
        }

    def activate_style(self, style_key: str):
        style = production_style(style_key)
        self.loaded_adapters = ()          # unload first, always
        self.loaded_adapters = (style.key,)
        self.active_style = style.key
        self.switch_log.append(style.key)
        return style

    def generate(self, **kwargs) -> GenerationOutcome:
        self.loaded = True
        if self.before_generate is not None:
            self.before_generate()
        style = self.activate_style(kwargs["style_key"])
        self.calls.append(kwargs)

        if self.fail_with is not None:
            failure, self.fail_with = self.fail_with, None
            # A failed generation must still leave clean state behind.
            self.scale_history.append(0.55)
            raise failure

        reference_present = kwargs.get("reference_image") is not None
        scale = float(kwargs["ip_adapter_scale"]) if reference_present else 0.0
        self.scale_history.append(scale)

        buffer = io.BytesIO()
        Image.new("RGB", (8, 24), (10, 20, 30)).save(buffer, format="PNG")
        png = buffer.getvalue()
        return GenerationOutcome(
            image_png=png,
            image_sha256="0" * 64,
            prompt=f"{style.trigger} {style.phrase} skateboard decal artwork, "
            + kwargs["subject_prompt"],
            seed=int(kwargs["seed"]),
            steps_run=30,
            generate_seconds=0.01,
            load_seconds=0.0,
            peak_allocated_mb=5143.73,
            peak_reserved_mb=5200.0,
            allocated_before_mb=2066.56,
            allocated_after_mb=2066.56,
            reserved_before_mb=2100.0,
            reserved_after_mb=2100.0,
            device_used_mb=7985.5,
            process_rss_mb=1000.0,
            active_adapters=self.loaded_adapters,
            live_lora_modules=128,
            ip_adapter_scale_applied=scale,
            reference_present=reference_present,
            adapter_sha256=style.sha256,
        )


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(generated_dir=tmp_path / "generated")


@pytest.fixture
def fake_pipeline() -> FakePipeline:
    return FakePipeline()


@pytest.fixture
def service(settings, fake_pipeline) -> GenerationService:
    return GenerationService(settings, pipeline=fake_pipeline)


@pytest.fixture
def client(service):
    from fastapi.testclient import TestClient

    from apps.api.main import create_app

    return TestClient(create_app(service))


@pytest.fixture
def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), (200, 100, 50)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def style_keys() -> list[str]:
    return [s.key for s in PRODUCTION_STYLES]


class Gate:
    """Blocks a generation inside the lock so a second request can be tried."""

    def __init__(self) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()

    def __call__(self) -> None:
        self.entered.set()
        assert self.release.wait(timeout=10), "gate was never released"
