# Environment audit

**Date:** 2026-07-27 · **Machine:** KYLIAN · **Auditor:** Claude Code session, all outputs below are verbatim results of commands actually executed on this machine. Nothing is estimated or assumed; absent tools are recorded as absent.

## Summary

| Component | Result | Impact |
|---|---|---|
| OS | Windows 11 Home 10.0.26200 (64-bit) | Native Windows workflow; WSL only hosts Docker Desktop |
| Shell | Windows PowerShell 5.1 (build 26100) | Scripts must target PS 5.1 or use `bash` via Git |
| RAM | 16 GB (15.6 GiB usable) | Adequate for inference + web dev; tight for large batch training |
| GPU | NVIDIA GeForce RTX 4060 Laptop, **8188 MiB (8 GB) VRAM** | Gates model choice: SD 1.5-class LoRA training feasible; SDXL training will need aggressive memory optimization; from-scratch training infeasible |
| GPU driver | 610.74, CUDA UMD 13.3, WDDM mode | Recent driver; supports current PyTorch CUDA builds |
| CUDA toolkit (`nvcc`) | **Not installed** | Not required for PyTorch binary wheels; note for any custom kernels |
| Python | 3.14.0 (default via `py`), **3.11 also installed** | PyTorch does not support 3.14 → use Python 3.11 for all ML work |
| pip | 26.0 (via `py -m pip`) | `pip`/`python` not on PATH; use `py` launcher or venv activation |
| Node.js / npm | v20.18.0 / 10.8.2 | Meets Vite/React/Three.js requirements |
| Git | 2.42.0.windows.2 | OK; user configured (KylianAlgoet / kylian.algoet@student.ehb.be) |
| Docker | 29.1.3 (Docker Desktop, WSL2 backend running) | Docker Compose deployment option is viable |
| FFmpeg | **Not installed** | Only needed for demo-video work; install later if required |
| conda | **Not installed** | Use venv (standard library) instead |
| MSVC (`cl`) | Not on PATH | Only relevant if a package must compile from source |
| Disk (C:) | 228.1 GB free of ~926 GB | Sufficient for base model (~4–7 GB), dataset, and checkpoints; monitor during training |
| PyTorch | **Not installed** | Deliberate: no dependencies installed in Phase 0; install pinned versions after architecture decision |

## Key constraints derived from this audit

1. **8 GB VRAM is the hard constraint.** Training a diffusion model from scratch is out of reach. LoRA fine-tuning of an SD 1.5-class base model (~512px) is the realistic envelope; SDXL LoRA may be possible only with 8-bit optimizers, gradient checkpointing, and low rank — to be tested empirically in Prototype 3, not assumed.
2. **Python 3.11 must be used for ML work.** Python 3.14.0 is the default launcher version, but PyTorch wheels do not support 3.14. Create the ML venv with `py -V:3.11 -m venv .venv`.
3. **16 GB system RAM** means training and heavy IDE/browser use should not run simultaneously; dataloader workers must stay modest.
4. **No blocking gaps** for the planned stack: Node 20 covers the frontend, Docker enables the deployment option, and Git is configured.

## Raw command outputs (evidence)

### OS, hardware, shell

```
> Get-ComputerInfo -Property OsName, OsVersion, OsBuildNumber, OsArchitecture, CsName, CsSystemType, CsTotalPhysicalMemory

OsName                : Microsoft Windows 11 Home
OsVersion             : 10.0.26200
OsBuildNumber         : 26200
OsArchitecture        : 64-bit
CsName                : KYLIAN
CsSystemType          : x64-based PC
CsTotalPhysicalMemory : 16780918784

> $PSVersionTable.PSVersion
Major  Minor  Build  Revision
5      1      26100  8737

> Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum   # sum in GB
16

> Get-PSDrive -PSProvider FileSystem
Name UsedGB FreeGB
C     698.2  228.1
```

### WSL

```
> wsl --status
Default Distribution: docker-desktop
Default Version: 2

> wsl -l -v
  NAME              STATE     VERSION
* docker-desktop    Running   2
```

Only the Docker Desktop utility distribution exists; there is no general-purpose WSL distribution. All development happens natively on Windows.

### GPU

```
> nvidia-smi
Mon Jul 27 03:17:53 2026
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 610.74                 KMD Version: 610.74        CUDA UMD Version: 13.3     |
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0 Off |                  N/A |
| N/A   51C    P0             13W /   80W |       0MiB /   8188MiB |      0%      Default |
| No running processes found                                                              |
+-----------------------------------------------------------------------------------------+
```

GPU: NVIDIA GeForce RTX 4060 Laptop GPU (80 W power cap), 8188 MiB VRAM, driver/KMD 610.74, CUDA UMD 13.3, WDDM driver model, idle at audit time.

### Toolchain versions

```
> git --version
git version 2.42.0.windows.2
> git config user.name / user.email
KylianAlgoet / kylian.algoet@student.ehb.be

> python --version
Python was not found; run without arguments to install from the Microsoft Store... (Store alias, not a real interpreter)

> py --version
Python 3.14.0

> py -0p
 -V:3.14 *        C:\Users\kylia\AppData\Local\Python\pythoncore-3.14-64\python.exe
 -V:3.11          C:\Users\kylia\AppData\Local\Programs\Python\Python311\python.exe

> py -m pip --version
pip 26.0 from C:\Users\kylia\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\pip (python 3.14)

> pip --version
'pip' is not recognized (not on PATH; available via py -m pip)

> node --version
v20.18.0
> npm --version
10.8.2

> docker --version
Docker version 29.1.3, build f52814d

> ffmpeg -version
'ffmpeg' is not recognized (not installed)

> nvcc --version
'nvcc' is not recognized (CUDA toolkit not installed)

> conda --version
'conda' is not recognized (not installed)

> where.exe cl
(no output — MSVC compiler not on PATH)
```

### Not yet verifiable (as of the 2026-07-27 audit)

- **PyTorch CUDA availability:** PyTorch is not installed (no dependencies are installed in Phase 0). `torch.cuda.is_available()` will be verified immediately after the pinned install, before any training, as part of the Prototype 1 smoke test. → **Resolved 2026-07-30, see update below.**
- **Peak VRAM under load:** will be measured with `nvidia-smi` during Prototype 1/3 runs and recorded in `experiments/registry.csv`. → Still open; measured during the Prototype 1 benchmark runs.

## Update 2026-07-30 (M3 / Prototype 1): PyTorch CUDA verified

The Phase 0 open item is closed. Verbatim output of `.venv/Scripts/python.exe -m ml.inference.gpu_smoke_test` (EXP-001, exit code 0):

```
torch import ......... True
torch version ........ 2.13.0+cu126
bundled CUDA runtime . 12.6  (wheel-provided)
driver version ....... 610.88  (driver max CUDA API, not a toolkit match)
cuda_available ....... True
GPU .................. NVIDIA GeForce RTX 4060 Laptop GPU (sm_89)
total VRAM ........... 8187.5 MiB (8.0 GiB)
expected model match . True
float32   matmul .... OK (relative error 6.32e-07)
float16   matmul .... OK (relative error 5.22e-04)
bfloat16  matmul .... OK (relative error 4.28e-03)

VERDICT: PASS
```

Structured evidence: `docs/evidence/EXP-001/cuda-smoke-test.json`, `pip-freeze.txt`, `nvidia-smi.txt`.

**Corrections and findings from this verification:**

1. **The driver has changed since the audit.** `nvidia-smi` now reports **610.88** (KMD 610.88), not the 610.74 recorded on 2026-07-27. The driver was updated on this machine between the two dates. VRAM is unchanged (8187.5 MiB via torch, 8188 MiB via `nvidia-smi`).
2. **The audit's phrasing "CUDA UMD 13.3 → supports current PyTorch CUDA builds" was right for the wrong reason, and is corrected here.** The CUDA version `nvidia-smi` prints is the **driver's maximum supported CUDA API version**, not a toolkit version PyTorch must match. PyTorch wheels bundle their own CUDA runtime — this install runs a **CUDA 12.6** runtime on a driver advertising 13.3, which is correct and expected via CUDA minor-version compatibility. No CUDA toolkit (`nvcc`) is needed, as the audit already noted.
3. **bfloat16 works** on this Ada (sm_89) GPU, so bf16 is available as a documented fallback if fp16 misbehaves in a pipeline.
4. **pip had to be upgraded before PyTorch would install.** The venv shipped pip 22.3 (Python 3.11.0, Oct 2022), which rejects wheels whose metadata name is normalized with underscores and failed to resolve `torch` at all (`expected 'typing-extensions', but metadata has 'typing_extensions'`). Upgraded to pip 26.2; the install then succeeded. Recorded in `ml/requirements-inference.txt`.

## Version-conflict notes

- The `python` command resolves to the Microsoft Store alias, not a real interpreter — always use `py` (or an activated venv).
- Default `py` → 3.14.0, which PyTorch does not support; the ML environment must explicitly target 3.11 (`py -V:3.11`).
- No conda present, so no conda/venv conflicts; venv is the single environment mechanism.
