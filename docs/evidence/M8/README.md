# M8 evidence index

**Milestone:** M8 — testing, deployment, clean-clone validation and demo preparation
**Dates:** 2026-08-09 · **Status: COMPLETE**, all six acceptance criteria met.

## Acceptance criteria → evidence

| # | criterion (issue #9) | status | evidence |
|---:|---|---|---|
| 1 | Backend, frontend and E2E suites pass; results evidenced | **MET** | [`baseline/test-baseline.md`](baseline/test-baseline.md), [`tests/playwright-e2e-report.md`](tests/playwright-e2e-report.md) |
| 2 | Upload-security tests: malicious filename, oversize, wrong MIME | **MET** | [`security/upload-security-matrix.md`](security/upload-security-matrix.md) |
| 3 | Deployment decision recorded in a Decision Record | **MET** | [`DR-014`](../../decisions/DR-014-deployment-and-demo-strategy.md) |
| 4 | Clean-clone test succeeds with real output | **MET** | [`clean-clone/log.md`](clean-clone/log.md), [`clean-clone/real-output.md`](clean-clone/real-output.md) |
| 5 | Timed demo script written | **MET** | [`demo-script.md`](../../presentation/demo-script.md) |
| 6 | Backup demo plan written | **MET** | [`demo-backup-plan.md`](../../presentation/demo-backup-plan.md) |

## Final measured state

| gate | M7 close | M8 close |
|---|---:|---:|
| pytest | 406 | **473** |
| vitest | 165 | **169** |
| **Playwright E2E** | **0 — did not exist** | **37** |
| eslint | clean | clean |
| production build | succeeds | succeeds |

**Generation count: 27** — 25 research (closed at cap) + 1 M7 human review + 1 M8 deployment
validation. Never reported as 25.

## Files

```
baseline/test-baseline.md              the four gates re-measured before any M8 work
security/upload-security-matrix.md     27 rules mapped to tests, incl. what is NOT tested
tests/playwright-e2e-report.md         the 37-scenario E2E suite
tests/ci-workflow.md                   the CI workflow - and that it has never run
deployment/preflight-and-lifecycle.md  real output of all four PowerShell scripts
clean-clone/log.md                     18 ordered steps with real output
clean-clone/environment.md             versions measured INSIDE the clone
clean-clone/api-health.json            the health response from the clone
clean-clone/real-output.md             the one authorised generation
clean-clone/real-output/               metadata, run record, 3 screenshots
clean-clone/screenshots/               2 captures from the non-GPU pass
```

Also produced outside this directory: `docs/deployment/runbook.md`,
`docs/deployment/weights-manifest.md`, `docs/presentation/demo-script.md`,
`demo-backup-plan.md`, `demo-backup-manifest.md`, `docs/process/feature-freeze.md`,
`DR-014`, and four PowerShell scripts under `scripts/`.

## The five findings worth reading

M8 was supposed to verify, not discover. It found five real problems, all recorded rather than
quietly fixed.

1. **The frozen dataset hash failed on every clean clone.** `DATASET_V1_SHA256` was taken from a
   CRLF working copy while Git stores LF, so an integrity control had only ever passed on its
   author's machine. Fixed by separating the M6 *identifier* from the *content check* — repointing
   the original would have moved `kit_fingerprint()` and every run's `dataset_version`.
   → [`clean-clone/log.md`](clean-clone/log.md)
2. **`.env.example` documented five settings nothing reads**, two of which implied that upload
   security rules were configurable. → [`security/upload-security-matrix.md`](security/upload-security-matrix.md)
3. **The audited Node version was stale** — v20.18.0 recorded, v24.18.0 actual, with no record of
   when it changed. → [`baseline/test-baseline.md`](baseline/test-baseline.md)
4. **`apps/api/requirements.txt` claimed a pin it did not make.** Four "pinned" lines were comments;
   the clone resolved starlette 1.6.0. → [`clean-clone/environment.md`](clean-clone/environment.md)
5. **`uvicorn --workers 1` starts two processes**, so `/api/health` reports a PID that is not the
   one the launcher recorded, and a naive stop leaves the worker holding port 8000.
   → [`deployment/preflight-and-lifecycle.md`](deployment/preflight-and-lifecycle.md)

## The result worth remembering

**The clean clone reproduced M7's Phase A output byte-for-byte** — sha256 `46bbf160e427…`,
1 089 939 bytes, same seed and settings, a freshly built environment three days later.

Inference is deterministic and portable given a fixed adapter. **This does not contradict R14**,
which is about *training* not being reproducible from seed — different halves of the pipeline, both
statements true.

## What this evidence does NOT prove

No test in the pytest, vitest or Playwright suites loads the model. They prove the code, the
contracts and the interface. Generation quality, VRAM, latency and adapter integrity under real
serving are evidenced separately — `experiments/registry.csv`, EXP-034, EXP-035,
`scripts/validate_p5_api.py` and the single clean-clone generation. Neither kind of evidence is
presented as the other.
