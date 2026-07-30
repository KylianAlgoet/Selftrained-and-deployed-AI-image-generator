"""Regression tests for the benchmark's resource sampler.

These exist because of a real defect found by the one-image smoke test: the
sampler stored its stop flag as `self._stop`, shadowing `threading.Thread._stop()`
- an internal method that `join()` calls - so every `stop()` raised
"'Event' object is not callable" and destroyed the result row of a run that had
already succeeded.

Runs on CPU with injected stubs: `ml.inference.benchmark` imports torch and
diffusers only inside functions, so the sampler is testable without a GPU.
"""

from ml.inference.benchmark import ResourceSampler

MIB = 1024**2


class FakeCuda:
    def __init__(self, samples):
        self._samples = list(samples)

    def mem_get_info(self):
        # (free, total) - device used is total - free, as nvidia-smi reports.
        return self._samples.pop(0) if len(self._samples) > 1 else self._samples[0]


class FakeTorch:
    def __init__(self, samples):
        self.cuda = FakeCuda(samples)


class FakeProcess:
    def __init__(self, rss_values):
        self._values = list(rss_values)

    def memory_info(self):
        value = self._values.pop(0) if len(self._values) > 1 else self._values[0]
        return type("MemInfo", (), {"rss": value})()


def test_stop_does_not_raise_and_thread_terminates():
    """The exact bug: stop() must survive join()."""
    sampler = ResourceSampler(FakeTorch([(4 * MIB, 8 * MIB)]), FakeProcess([100 * MIB]), interval=0.01)
    sampler.start()
    sampler.stop()
    assert not sampler.is_alive()


def test_records_peak_not_last_value():
    samples = [(6 * MIB, 8 * MIB), (2 * MIB, 8 * MIB), (7 * MIB, 8 * MIB)]  # used: 2, 6, 1
    sampler = ResourceSampler(FakeTorch(samples), FakeProcess([50 * MIB, 300 * MIB, 80 * MIB]), interval=0.01)
    sampler.start()
    import time

    time.sleep(0.1)
    sampler.stop()
    assert sampler.peak_device_used_mb >= 6.0
    assert sampler.peak_process_rss_mb >= 300.0


def test_short_run_still_gets_at_least_one_sample():
    """A generation faster than the sample interval must not report zero."""
    sampler = ResourceSampler(FakeTorch([(4 * MIB, 8 * MIB)]), FakeProcess([123 * MIB]), interval=60)
    sampler.start()
    sampler.stop()
    assert sampler.peak_device_used_mb == 4.0
    assert sampler.peak_process_rss_mb == 123.0


def test_sampling_errors_never_propagate():
    """Instrumentation must not be able to fail a benchmark run."""

    class ExplodingTorch:
        class cuda:  # noqa: N801
            @staticmethod
            def mem_get_info():
                raise RuntimeError("no device")

    class ExplodingProcess:
        @staticmethod
        def memory_info():
            raise RuntimeError("gone")

    sampler = ResourceSampler(ExplodingTorch(), ExplodingProcess(), interval=0.01)
    sampler.start()
    sampler.stop()
    assert sampler.peak_device_used_mb == 0.0
    assert sampler.peak_process_rss_mb == 0.0
    assert not sampler.is_alive()
