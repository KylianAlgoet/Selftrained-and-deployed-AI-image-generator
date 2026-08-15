# DeckForge AI — setup and demo runbook

**Milestone:** M8 · **Decision:** [DR-014](../decisions/DR-014-deployment-and-demo-strategy.md)
**Validated by:** the clean-clone test in `docs/evidence/M8/clean-clone/`

Native local deployment on a Windows machine with an NVIDIA GPU. There is no container and no
cloud component — see DR-014 for why, including what was screened out rather than benchmarked.

## Prerequisites

| requirement | validated version | why it is required |
|---|---|---|
| Windows | 11 Home 10.0.26200 | PowerShell scripts target PS 5.1 |
| **NVIDIA GPU, ~8 GB VRAM** | RTX 4060 Laptop, 8188 MiB, driver 610.88 | The stack peaks at 7985.5 MiB. **There is no CPU fallback.** |
| Python **3.11** | 3.11.0 | PyTorch publishes no wheels for 3.14, which is this machine's default `py` |
| Node.js **>= 20.19** | 24.18.0 | Vite 6 / the frontend toolchain |
| Git | 2.42.0 | |
| **The three LoRA adapters** | 6 414 480 bytes each | Not in Git, **not regenerable** — see [weights-manifest.md](weights-manifest.md) |

Disk: ~6 GB for the Hugging Face cache (base model + IP-Adapter, downloaded on first use to
`C:\Users\<user>\.cache\huggingface`), plus ~500 MB for the Python environment.

## First-time setup

```powershell
# 1. Clone
git clone https://github.com/KylianAlgoet/Selftrained-and-deployed-AI-image-generator.git
cd Selftrained-and-deployed-AI-image-generator

# 2. Python 3.11 environment. `py -V:3.11` is mandatory - the default is 3.14.
py -V:3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip

# 3. Dependencies, in this order.
#    PyTorch does NOT come from PyPI - the CUDA build lives on its own index.
.\.venv\Scripts\python.exe -m pip install torch==2.13.0+cu126 torchvision==0.28.0+cu126 `
    --index-url https://download.pytorch.org/whl/cu126
.\.venv\Scripts\python.exe -m pip install -r ml\requirements.txt
.\.venv\Scripts\python.exe -m pip install -r ml\requirements-inference.txt
.\.venv\Scripts\python.exe -m pip install -r ml\requirements-training.txt
.\.venv\Scripts\python.exe -m pip install -r apps\api\requirements.txt

# 4. Frontend, from the lockfile
cd apps\web
npm ci
cd ..\..

# 5. Restore the production adapters and verify them
.\scripts\verify-weights.ps1 -RestoreFrom "<your backup path>"
```

**`pip` must be upgraded before installing torch.** The venv ships pip 22.3, which rejects wheels
whose metadata name is underscore-normalised and cannot resolve `torch` at all. This is a real
failure recorded in M3, not a precaution.

### If the adapters are somewhere else

```powershell
$env:CHECKPOINT_ROOT = "E:\DeckForge-weights"
```

The service resolves `<CHECKPOINT_ROOT>\outputs\lora\...` and defaults to the repository root, so
the ordinary case needs no configuration.

## Running it

```powershell
.\scripts\preflight.ps1      # verify everything before starting anything
.\scripts\start-demo.ps1     # API + frontend, prints the URL
# ... demonstrate ...
.\scripts\stop-demo.ps1      # stop only what was started, verify ports released
```

`start-demo.ps1 -Preview` serves the built frontend on 4173 instead of the dev server on 5173.

### Or manually

```powershell
.\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 1
cd apps\web; npm run dev
```

**`--workers 1` and no `--reload` are correctness requirements, not preferences.** The busy lock is
process-local and a second resident pipeline does not fit in the ~200 MiB of spare VRAM; the
reloader runs a second process that would hold the same GPU.

## What "one worker" actually looks like

Measured during M8, and worth knowing before you look at Task Manager mid-demo:

```
python.exe  19700   <- uvicorn supervisor; loads NO model
python.exe   8632   <- the worker; this is the one that serves and holds the pipeline
```

`uvicorn --workers 1` starts a supervisor **and** one worker, so you will see **two** `python.exe`
processes. That is correct and is not a duplicated API: only the worker loads the model, and
`GET /api/health` reports the **worker's** PID (8632 above), which is deliberately not the PID
`start-demo.ps1` records for the process it launched (19700, the supervisor). `stop-demo.ps1`
stops the child as well as the parent, which is why it stops the tree rather than one PID.

## Verifying it is up

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Expect `status: ok`, `cuda_available: true`, `single_worker_guard: enforced`, and
**`pipeline_loaded: false`** — the model loads lazily on the first generation request, so a fresh
service holds no GPU memory (`allocated_mb: 0.0`).

Then open the printed URL. The deck renders with a starter decal immediately; nothing about the
3D preview needs the model.

## Timings to expect

| action | time |
|---|---|
| service start | ~2 s (no model loaded) |
| **first** generation | **~30 s** — includes the one-off model load |
| later generations | **~13 s** |
| uploading your own decal | instant, **no GPU, no server round trip** |

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest        # 527, no GPU, pipeline stubbed
cd apps\web
npm run test                                # 183 vitest
npm run lint
npm run build
npx playwright test                         # 38 E2E, no GPU, no model
```

The pytest total is **473 system + 16 report-validation + 38 deck-validation**. Only the first
473 test the application; the other 54 test the report and the deck. Counts measured 2026-08-15
(M11), and they supersede the 461/169/37 figures this section carried from M8.

Playwright needs its browser once: `npx playwright install chromium`.

## Troubleshooting

| symptom | cause | fix |
|---|---|---|
| `REFUSING TO START. Port 8000 is already held` | an API process is already running | `.\scripts\stop-demo.ps1`, or `-Force` |
| **503 `model_unavailable`** | an adapter is missing or fails its SHA-256 | `.\scripts\verify-weights.ps1`. **Restore from backup — never retrain (R14).** |
| **409 `generation_in_progress`** | another generation holds the GPU | Wait ~13 s. This is the design working, not a fault. |
| **504 after N of 30 steps** | the generation exceeded `GENERATION_TIMEOUT_SECONDS` | Usually a cold first request. Retry; the second is warm. |
| `ConfigurationError: WEB_CONCURRENCY=…` | a worker-count variable is above 1 | Unset it. One worker is a hard requirement. |
| Frontend shows "Could not reach the generation service" | the API is not running or CORS blocks it | Start the API; check `ALLOWED_ORIGINS` matches the frontend origin. |
| `torch.cuda.is_available()` is False | driver or GPU unavailable | Check `nvidia-smi`. Without CUDA the application cannot generate. |
| pip cannot resolve `torch` | pip 22.3 in a fresh venv | `python -m pip install --upgrade pip` |

## Configuration

All optional; see `.env.example`, which documents only variables the code actually reads.
`API_HOST`, `API_PORT`, `ALLOWED_ORIGINS`, `MAX_UPLOAD_SIZE_MB`, `GENERATION_TIMEOUT_SECONDS`,
`DEFAULT_SEED`, `GENERATED_OUTPUT_DIR`, `CHECKPOINT_ROOT`, and `VITE_API_BASE_URL` /
`VITE_REVIEW_MODE` on the frontend.

**Do not set `WEB_CONCURRENCY`, `UVICORN_WORKERS` or `GUNICORN_WORKERS` above 1.** They are read
only in order to be rejected.

## Known limitations, carried openly

1. Cold model loading has **no honest percentage** — it reports a stage and no number.
2. The ETA is approximate and covers **measured denoising** only.
3. "Finalising" may be visible only briefly, and is deliberately not padded.
4. **Prompt adherence can be weaker than style adherence** — strong style conditioning can dominate
   detailed prompt content. Measured in M6, accepted in M7, not a frontend fault.
5. The GPU margin is **~200 MiB**. This is not comfortable headroom.
6. **One API process, one worker, one generation at a time.** Not scalable, by design.
7. `retro-poster` is a **PARTIAL PASS** and warns on every request.
