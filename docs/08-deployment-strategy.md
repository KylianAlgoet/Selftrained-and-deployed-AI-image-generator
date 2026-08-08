# Deployment strategy

**Created:** 2026-07-27 · **Updated:** 2026-08-09 (M8) · **Status:** **DECIDED — see
[`DR-014`](decisions/DR-014-deployment-and-demo-strategy.md).**

> **Decision (2026-08-09, DR-014): native local deployment on the validated Windows/NVIDIA machine,
> plus pre-generated backup demo assets** — Option A combined with the demo-readiness section
> below. Docker (Option B) was **screened out, not benchmarked**: its GPU overhead against the
> measured 200.0 MiB margin is unmeasured, GPU passthrough was never verified on this machine, and
> no NVIDIA Container Toolkit is installed. It would also not solve the actual reproducibility
> problem, which is the three unregenerable adapter files (R14), not the Python environment.
> Cloud GPU (Option C) was rejected on cost, offline capability, and because different hardware
> would invalidate every VRAM figure in the research.
>
> Runbook: [`docs/deployment/runbook.md`](deployment/runbook.md). Weights:
> [`docs/deployment/weights-manifest.md`](deployment/weights-manifest.md). Clean-clone evidence:
> `docs/evidence/M8/clean-clone/`.
>
> The candidate table below is preserved as it was written, before the MVP existed, because the
> comparison it framed is part of the process record.

## Requirement

A reproducible deployment **or demonstration** setup: a third party (or the jury) can follow documented steps on suitable hardware and run the full system, or the student can demonstrate it live with a verified, repeatable procedure.

## Candidates

| Option | Sketch | Pros | Cons / open questions |
|---|---|---|---|
| A. Documented two-process local run | `py -V:3.11` venv + `uvicorn` for API; `npm run dev`/`preview` for web; README runbook + clean-clone test | Simplest; no GPU-in-container issues; matches demo hardware | Reproducibility depends on runbook quality; validated by clean-clone test |
| B. Docker Compose | API + web containers; GPU passthrough via Docker Desktop WSL2 | Strong reproducibility story; Docker 29.1.3 available (audit) | GPU passthrough on Windows Docker Desktop must be verified; image size with CUDA stack; time cost |
| C. Hybrid | Web + API in Compose, model inference on host | Balances A and B | Extra moving parts for marginal benefit |

## Decision criteria (applied in M8)

Clean-clone success rate, setup time, GPU accessibility, demo reliability on the presentation machine, and remaining schedule. The decision gets a DR record and the chosen path is validated by an actual clean-clone test documented with real output.

## Demo readiness (M8/M10)

Whatever the choice: a timed demo script, pre-generated backup outputs, and a backup demo plan (recorded video + local screenshots) in case live generation fails on stage.
