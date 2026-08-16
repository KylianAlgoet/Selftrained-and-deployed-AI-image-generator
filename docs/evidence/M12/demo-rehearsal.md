# M12 — post-M11 demo rehearsal, and the GPU crash that preceded it

**Date:** 2026-08-16 · **Machine:** the audited RTX 4060 Laptop GPU
(`docs/technical/environment-audit.md`) · **Authorised by:** Kylian Algoet

This record exists because two things happened after the M11 close that the M11 records cannot
describe without being falsified: a **failed** GPU inference attempt that crashed the machine, and
**three completed** generations during the demo rehearsal that followed.

**M11's own numbers are not edited.** `docs/evidence/M11/gpu-validation.md` still reads
**28**, and `docs/evidence/M8/README.md` still reads **27**, because both were true when written.
This file carries the new current total, and `report/facts.yaml` re-points `generations_total`
here — the same mechanism used when the lock moved from the M8 record to the M11 record, recorded
in `docs/learning-outcome-traceability.md` and `docs/process/process-log.md`.

## 1. The failed attempt — VIDEO_TDR_FAILURE

A generation was started from the running application and **never completed**. The machine froze
and rebooted. Windows recorded a bugcheck.

| fact | value | source |
|---|---|---|
| bugcheck | `0x00000116` (VIDEO_TDR_FAILURE) | System log, WER-SystemErrorReporting Id 1001, 16:01:57 |
| parameters | `0xffff9e03e6788010, 0xfffff8017d5da350, 0xffffffffc000009a, 0x0000000000000004` | same |
| named driver | **`nvlddmkm.sys`** | WER-SystemErrorReporting Id 1019, 16:01:57 |
| dump | `C:\WINDOWS\Minidump\081626-25859-01.dmp`, report id `a1854378-ab70-4240-88b3-007748d6d86f` | same |
| unclean shutdown | Kernel-Power Id 41, Critical, 16:01:36 | System log |
| freeze window | **after 15:56:53, before 16:01:32** | `.run/demo.json` was written at 15:56:53; OS start 16:01:32 |
| WHEA hardware errors | **none in the preceding 7 days** | `Microsoft-Windows-WHEA-Logger` query returned no events |
| preceding state | resumed from a ~10 h sleep at 15:44:52 | Power-Troubleshooter Id 1 |

**This attempt produced no PNG.** It is counted as a failed attempt (tallied in §4) and is
deliberately **not** part of the completed-generation total.

**The cause was not established.** The driver that failed is named by Windows, but *why* the GPU
hung is unknown: `C:\Windows\Minidump` and the WER report bodies are not readable without
elevation, and no minidump analysis was performed. The `0xC000009A`
(`STATUS_INSUFFICIENT_RESOURCES`) parameter is the status reported during the failed reset and is
**not** evidence that VRAM was exhausted. Recorded as unexplained rather than guessed.

## 2. Recovery, before anything was re-run

| step | result |
|---|---|
| `scripts/stop-demo.ps1` | stale `.run/demo.json` cleared; ports 8000 / 5173 / 4173 released; exit 0 |
| GPU after reboot | `nvidia-smi` 610.88, **0 MiB used**, 52 °C, P8, no compute apps; `Win32_VideoController` status OK, `ConfigManagerErrorCode 0`; PnP `CM_PROB_NONE` |
| `scripts/preflight.ps1` | **10 of 10 PASS**, 0 warnings — including **all three adapters matching their recorded sha256**, so the crash corrupted nothing |
| `scripts/start-demo.ps1` | API and frontend started; `single_worker_guard` enforced |

## 3. The three completed generations

All three are **512 × 1536** — the production deck format — and all were produced through the
running application on the audited GPU.

| # | file (`outputs/api/`) | written | bytes | sha256 |
|---:|---|---|---:|---|
| 1 | `xKu-ZW3n-q8qd9BfA6g5kQ.png` | 16:19:02 | 1 684 829 | `3b68f09886e7e7b26ce1b8de82b4d0b057ae961a463cccc6830dd0a920c0e302` |
| 2 | `4qWHqoXJbKWulsmnsw_vCQ.png` | 16:21:42 | 1 267 911 | `223d2edc07edc266feae279ae43ae1c4d7409016b3e52217f7681d95ed8df489` |
| 3 | `pPE2JPJ18NMrAc-GS53Dng.png` | 16:22:50 | 1 452 493 | `3c3ebac26e20a924e266a4a31f4e4a66e404af78a35950381f3f9bf55bdaf3c7` |

The last run reported **30 of 30 steps in 13.7 s** (`GET /api/generation-progress`), consistent
with the 12–13 s steady-state figure the project already documents. The API's single-flight lock
makes concurrent runs impossible, so these were three sequential runs.

Kylian records the rehearsal prompt as **"Mount Fuji under a red sun"** in the **Ukiyo-e woodblock**
style, with no reference image. The active style at the end of the session was `ukiyo-e`
(`GET /api/health`).

### What is missing, and why it is not reconstructed

**The full `GenerationMetadata` block was not captured for these three outputs.** This is a real
gap in the evidence and is recorded rather than filled in:

- metadata is held only in the API process's memory (`apps/api/generation.py:63`) and is returned
  once, in the `POST /api/generate` response
- the PNGs carry **no embedded text metadata** — verified by opening all three
- no endpoint reads it back: `GET /api/generated/{id}` returns image bytes only
  (`apps/api/main.py:280`)
- the frontend holds a single `result` (`apps/web/src/App.tsx:69`), overwritten on each run, so by
  the time the gap was noticed the earlier two were already gone

Consequently **seed, guidance scale, scheduler, adapter checkpoint, prompt hash and peak VRAM are
not known for any of the three**, and no attempt is made to infer them. Which file corresponds to
which prompt is also not evidenced. What *is* evidenced — existence, timing, format, byte size and
sha256 — is above.

This contrasts deliberately with the M11 validation, where the sha256 was declared *before* the run
and matched afterwards. **These three are demonstration outputs, not experimental evidence, and
they support no research claim.** No RQ conclusion, rubric score or experiment result depends on
them.

## 4. The current total

25 research (closed at cap) + 1 M7 human review + 1 M8 deployment validation + 1 M11 final-audit
validation + 3 M12 demo rehearsal.

**Generation count: 31**

Plus, separately and not included above: **1 failed GPU inference attempt** (§1).

## 5. Consequences

- No retraining, no model change, no code change followed this session.
- The three adapters were re-verified by sha256 during preflight after the crash and are unchanged.
- The presentation was checked and **not** rebuilt: no slide states a generation total.
- `report/facts.yaml` re-points `generations_total` to this file. Historical records keep their
  historical numbers.
