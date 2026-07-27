# Deployment strategy

**Created:** 2026-07-27 · **Status:** candidates defined; decision deferred to milestone M8 (RQ12), after the MVP exists.

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
