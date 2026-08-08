# DR-014 — Deployment and demonstration strategy

**Status:** accepted · **Date:** 2026-08-09 · **Milestone:** M8
**Answers:** RQ12 — how is a locally trained, GPU-bound generator deployed so that it is
reproducible for a third party and reliable for a live bachelor demonstration?
**Related:** DR-001 (monorepo), DR-002 (FastAPI), DR-011 (service architecture), DR-010 (per-style
adapters), R12 (memory margin), R14 (checkpoints are unregenerable artifacts)
**Evidence:** EXP-019b, EXP-032, EXP-034, `docs/technical/environment-audit.md`,
`docs/evidence/M8/clean-clone/`, `docs/evidence/prototype-5/api-validation.jsonl`
**Supersedes:** the candidate list in `docs/08-deployment-strategy.md` (2026-07-27), which
deliberately deferred this decision to M8 "after the MVP exists".

## Context

Every candidate in the 2026-07-27 sketch was written before the system existed. Three measured
facts have arrived since, and they constrain this decision far more than the original criteria did.

1. **The memory margin is 200.0 MiB of 8187.5 MiB — 2.4 % of the device.** EXP-034 measured the
   worst spare under real serving conditions, tighter than EXP-032's 202.0 MiB. This is **not
   comfortable headroom**, and anything added to the production path has to fit inside it.
2. **The service is single-process by design, not by omission.** The busy lock is a
   `threading.Lock` and is process-local; a second resident pipeline does not fit at all (DR-011).
   Scaling is therefore not a configuration change, and any deployment that multiplies processes is
   wrong rather than merely inefficient.
3. **The production checkpoints cannot be rebuilt from source.** R14: LoRA initialisation drew from
   an unseeded global RNG during M6, so the three adapters are **authoritative as files, by
   SHA-256**. A clean clone can reproduce the code and the environment but *cannot* reproduce the
   weights. Any deployment story that pretends otherwise is false.

The requirement, from `docs/08-deployment-strategy.md`, is a reproducible deployment **or
demonstration** setup: a third party can follow documented steps on suitable hardware and run the
system, or the student can demonstrate it live with a verified, repeatable procedure.

## Alternatives

### A — Documented native local run on the validated machine
Python 3.11 venv + `uvicorn --workers 1`, `npm run dev`/`preview`, a runbook, preflight and
start/stop scripts, weights restored from an external backup and verified by SHA-256.

### B — Docker Compose with GPU passthrough
API and web containers, GPU via Docker Desktop's WSL2 backend and the NVIDIA Container Toolkit.

### C — Public cloud GPU deployment
A rented GPU instance serving the application publicly.

### D — Native local **plus pre-generated backup demo assets**
A, with a verified fallback set (a real generated PNG, its metadata, the existing screenshot set)
and the `Upload your own decal` path as a live fallback that needs no GPU.

## Criteria and comparison

| criterion | A | B | C | **D** |
|---|---|---|---|---|
| demo-day reliability | high | medium | medium (network) | **highest** |
| reproducibility for a third party | good, via runbook + clean-clone proof | good in principle | poor | good |
| GPU compatibility | **validated** (EXP-034) | **unverified on this machine** | different hardware | **validated** |
| VRAM overhead against 200.0 MiB | **zero** | non-zero, **unmeasured** | n/a | **zero** |
| complexity / setup time | low | high | high | low |
| cost | none | none | **paid** | none |
| offline capability | yes | yes | **no** | yes |
| clean-clone reproducibility | provable | needs its own proof | n/a | **proven** |
| risk | low | medium-high | medium | **lowest** |

## Decision

**Option D: reproducible native local deployment on the validated Windows/NVIDIA machine, with
pre-generated backup demo assets and a non-GPU live fallback.**

Concretely:

- **`uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 1`, no `--reload`.** One
  worker is a correctness requirement enforced in code (`config.assert_single_worker`).
- **Weights restored from an external backup**, located by a parameter or `CHECKPOINT_ROOT`, never
  by a private absolute path baked into the instructions. Verified by SHA-256 on restore
  (`scripts/verify-weights.ps1`) *and* on every style activation (`styles.verify_checkpoint`).
- **`scripts/preflight.ps1`** validates interpreter, Node, GPU, free ports and weights before
  anything starts; `start-demo.ps1` refuses to start if port 8000 is already held.
- **Validated by an actual clean-clone test** into a directory outside the repository, recorded in
  `docs/evidence/M8/clean-clone/`.
- **The demo carries backup assets** and can fall back to `Upload your own decal`, which needs no
  GPU, no model and no server round trip.

## Why Docker was rejected — on evidence, not on taste

Docker was the reproducibility-shaped answer and it is genuinely attractive on paper. It is
rejected for three measured reasons.

1. **Its GPU overhead against a 200.0 MiB margin is unmeasured — and measuring it would cost
   generations this project does not have.** The research budget closed at 25/25. A container
   runtime whose memory cost is unknown, sitting in front of the one number the entire project
   rests on, is an unquantified OOM risk introduced during the milestone whose purpose is to remove
   risk.
2. **GPU passthrough is unverified on this machine.** The audit records Docker Desktop 29.1.3 with
   a WSL2 backend, and **no NVIDIA Container Toolkit**. The 2026-07-27 sketch listed
   "GPU passthrough on Windows Docker Desktop must be verified" as an open question. It was never
   verified, so adopting B would mean adopting an unanswered question at the freeze.
3. **It would buy reproducibility of the part that is already reproducible.** The hard part of
   reproducing DeckForge AI is not the Python environment — that is pinned, and the clean-clone
   test proves it installs. The hard part is the **three unregenerable adapter files** (R14), and a
   container image does not solve that. It would either exclude them, leaving exactly the same
   restore-and-verify step, or embed 19 MB of weights the repository deliberately does not track.

**This is not a claim that Docker is unsuitable in general, or that it was measured and lost.** It
was screened out on hardware-verification and risk grounds and **never benchmarked here**; the
report must say that rather than implying a comparison that did not happen.

Cloud GPU (C) is rejected on cost, on losing offline capability for a live presentation, and
because different hardware would invalidate every VRAM figure the research rests on — an
RTX 4060 Laptop with 8 GB is not incidental to this project, it is the constraint the whole
investigation is about.

## Consequences

- **Reproducibility depends on runbook quality**, which is the honest weakness of Option A. The
  clean-clone test is what converts that dependency from a claim into evidence, and it is an M8
  acceptance criterion for exactly that reason.
- **A third party needs an NVIDIA GPU with ~8 GB VRAM.** The application does not run on CPU in any
  usable time, and no CPU fallback is offered or implied.
- **A third party also needs the three adapter files**, which are not in Git and cannot be
  regenerated (R14). `docs/deployment/weights-manifest.md` states their exact paths, sizes and
  hashes so a missing or wrong file fails loudly instead of silently serving something else.
- **The demonstration does not depend on the network**, and does not depend on a successful
  generation either: the 3D preview works from an uploaded decal with the model absent.
- **Deployment is not scalable and is not presented as such.** One process, one worker, one
  generation at a time, refused with 409 rather than queued. That is a measured consequence of
  8 GB, not an unfinished feature.
- **No container, orchestration or cloud artifact is produced by this project.** If a future
  version needs multi-user serving, it needs a different device before it needs a different
  deployment.
