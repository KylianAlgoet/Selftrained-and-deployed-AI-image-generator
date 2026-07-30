"""EXP-001: isolated PyTorch CUDA verification - the M3 hard gate.

Closes the open item in docs/technical/environment-audit.md ("PyTorch CUDA
availability: will be verified immediately after the pinned install"). Nothing
downstream in Prototype 1 may run until this script exits 0.

Deliberate distinction recorded in the evidence: the CUDA version reported by
`nvidia-smi` is the *driver's* maximum supported API version, NOT a toolkit
version that PyTorch must match. PyTorch wheels ship their own CUDA runtime
(`torch.version.cuda`). Both are captured so the difference is visible rather
than conflated.

Run:
    .venv/Scripts/python.exe -m ml.inference.gpu_smoke_test
"""

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "docs" / "evidence" / "EXP-001"
OUTPUT_JSON = EVIDENCE / "cuda-smoke-test.json"

EXPECTED_GPU_SUBSTRING = "4060"
# fp32 matmul is near-exact (TF32 is off by default for matmul in torch >= 1.12);
# fp16/bf16 accumulate visible error, so they are checked on relative terms.
TOLERANCES = {"float32": 1e-4, "float16": 2e-2, "bfloat16": 5e-2}
MATRIX_SIZE = 256


def nvidia_smi_snapshot() -> dict[str, str]:
    """Driver-side view. Absent tools are recorded as absent, never invented."""
    query = "driver_version,name,memory.total"
    try:
        out = subprocess.run(
            ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as err:
        return {"available": False, "error": f"{type(err).__name__}: {err}"}
    fields = [part.strip() for part in out.stdout.strip().splitlines()[0].split(",")]
    return {
        "available": True,
        "driver_version": fields[0],
        "gpu_name": fields[1],
        "memory_total": fields[2],
        "raw": out.stdout.strip(),
    }


def matmul_check(torch, dtype_name: str) -> dict:
    """Run a small CUDA matmul and compare against a float32 CPU reference."""
    dtype = getattr(torch, dtype_name)
    generator = torch.Generator(device="cpu").manual_seed(0)
    left = torch.randn(MATRIX_SIZE, MATRIX_SIZE, generator=generator)
    right = torch.randn(MATRIX_SIZE, MATRIX_SIZE, generator=generator)

    reference = (left @ right).to(torch.float32)
    try:
        actual = (left.to("cuda", dtype) @ right.to("cuda", dtype)).to("cpu", torch.float32)
    except Exception as err:  # noqa: BLE001 - the failure itself is the result
        return {"dtype": dtype_name, "ok": False, "error": f"{type(err).__name__}: {err}"}

    max_abs_diff = (actual - reference).abs().max().item()
    scale = reference.abs().max().item()
    relative_error = max_abs_diff / scale if scale else 0.0
    tolerance = TOLERANCES[dtype_name]
    return {
        "dtype": dtype_name,
        "ok": relative_error < tolerance,
        "matrix_size": MATRIX_SIZE,
        "max_abs_diff": max_abs_diff,
        "relative_error": relative_error,
        "tolerance": tolerance,
    }


def collect() -> dict:
    result: dict = {
        "experiment": "EXP-001",
        "purpose": "verify PyTorch CUDA availability on the audited RTX 4060 Laptop GPU",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "host": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
        },
        "nvidia_smi": nvidia_smi_snapshot(),
    }

    try:
        import torch
    except Exception as err:  # noqa: BLE001
        result["torch_import"] = {"ok": False, "error": f"{type(err).__name__}: {err}"}
        result["verdict"] = "FAIL"
        return result

    result["torch_import"] = {"ok": True}
    result["torch"] = {
        "version": torch.__version__,
        # Runtime bundled with the wheel - deliberately distinct from the driver's
        # reported CUDA API version above.
        "bundled_cuda_runtime": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version(),
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
    }

    if not torch.cuda.is_available():
        result["verdict"] = "FAIL"
        result["failure_reason"] = "torch.cuda.is_available() returned False"
        return result

    properties = torch.cuda.get_device_properties(0)
    total_bytes = properties.total_memory
    result["gpu"] = {
        "name": torch.cuda.get_device_name(0),
        "compute_capability": f"{properties.major}.{properties.minor}",
        "total_vram_bytes": total_bytes,
        "total_vram_mib": round(total_bytes / 1024**2, 1),
        "total_vram_gib": round(total_bytes / 1024**3, 2),
        "multi_processor_count": properties.multi_processor_count,
        "matches_expected_model": EXPECTED_GPU_SUBSTRING in torch.cuda.get_device_name(0),
    }
    result["dtype_checks"] = [matmul_check(torch, name) for name in ("float32", "float16", "bfloat16")]

    torch.cuda.synchronize()
    result["memory_after_checks"] = {
        "allocated_mib": round(torch.cuda.memory_allocated() / 1024**2, 2),
        "reserved_mib": round(torch.cuda.memory_reserved() / 1024**2, 2),
        "max_reserved_mib": round(torch.cuda.max_memory_reserved() / 1024**2, 2),
    }

    # bfloat16 is informational (it is a documented fallback if fp16 misbehaves);
    # the gate requires fp32 and fp16 to pass on the expected GPU.
    required = {check["dtype"]: check["ok"] for check in result["dtype_checks"]}
    result["verdict"] = (
        "PASS"
        if required.get("float32") and required.get("float16") and result["gpu"]["matches_expected_model"]
        else "FAIL"
    )
    return result


def main() -> int:
    result = collect()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(f"torch import ......... {result['torch_import']['ok']}")
    if "torch" in result:
        torch_info = result["torch"]
        print(f"torch version ........ {torch_info['version']}")
        print(f"bundled CUDA runtime . {torch_info['bundled_cuda_runtime']}  (wheel-provided)")
        smi = result["nvidia_smi"]
        if smi.get("available"):
            print(f"driver version ....... {smi['driver_version']}  (driver max CUDA API, not a toolkit match)")
        print(f"cuda_available ....... {torch_info['cuda_available']}")
    if "gpu" in result:
        gpu = result["gpu"]
        print(f"GPU .................. {gpu['name']} (sm_{gpu['compute_capability'].replace('.', '')})")
        print(f"total VRAM ........... {gpu['total_vram_mib']} MiB ({gpu['total_vram_gib']} GiB)")
        print(f"expected model match . {gpu['matches_expected_model']}")
    for check in result.get("dtype_checks", []):
        if check["ok"]:
            print(f"{check['dtype']:<9} matmul .... OK (relative error {check['relative_error']:.2e})")
        else:
            print(f"{check['dtype']:<9} matmul .... FAILED {check.get('error', check)}")
    print(f"\nVERDICT: {result['verdict']}")
    print(f"evidence: {OUTPUT_JSON}")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
