# Prototype 5 — final human visual gate: APPROVED

**Milestone:** M7 (Prototype 5 — integrated MVP) · **Gate:** final visual and functional
**Reviewer and approver:** Kylian Algoet · **Date:** 2026-08-07 · **Result: APPROVED**
**M7 is CLOSED LOCALLY.** Nothing was pushed; the remote issue and project board are untouched.

## 1. What was approved

| # | Item | Decision |
|---|---|---|
| 1 | The redesigned production interface | **APPROVED** |
| 2 | Real generation-progress and ETA implementation (DR-013) | **APPROVED** |
| 3 | `Upload your own decal` as a normal production feature | **APPROVED** |
| 4 | `full-surface` as the production texture-fit default (DR-012) | **APPROVED** (re-confirmed) |

## 2. Authoritative manual acceptance checklist

The twelve items of `GATE-handover.md` §12, completed live by Kylian across the functional
walkthrough and the final visual review.

| # | Item | Result |
|---|---|---|
| 1 | The style list shows three styles; `retro-poster` marked *(partial)* | **PASS** |
| 2 | Selecting `retro-poster` shows its limitation before generating | **PASS** |
| 3 | Generate with a prompt only; it completes and appears on the deck | **PASS** |
| 4 | The result panel shows adapter run, step, weight, seed and hashes | **PASS** |
| 5 | Same prompt and seed reproduce an identical image | **PASS** |
| 6 | Attaching a reference makes "Reference influence" adjustable | **PASS** |
| 7 | A `.exe` or `.gif` renamed to `.png` is refused with a clear message | **PASS** |
| 8 | Switching style generates in the new style; the previous does not linger | **PASS** |
| 9 | Compare the two texture-fit modes and choose the production default | **PASS** — `full-surface` selected, DR-012 |
| 10 | The inverted-UV demonstration flips nose/tail, confirming orientation | **PASS** |
| 11 | Download the PNG and the metadata JSON | **PASS** |
| 12 | Orbit and zoom, then generate again: the camera does not move | **PASS** |

**Result: 12 of 12 PASS. Final visual gate PASSED.**

## 3. Findings recorded at the gate

Reported by Kylian from the live review:

- The production interface reads as a professional skateboard artwork studio.
- The deck preview is visually dominant.
- The creation workflow is clear.
- The disabled Generate button and the loading information are readable.
- Cold model loading honestly showed **no fake percentage**.
- Real progress telemetry reached **30/30 diffusion steps** and was continuously delivered to the
  browser.
- **Finalising is intentionally brief and must not be artificially delayed.**
- The generated result, PNG download, metadata download and 3D texture application worked.
- The previous valid deck remained visible during generation.
- Review-only texture-fit and inverted-UV controls are hidden from normal production users.
- The user-uploaded decal feature is correctly separated from the AI reference-image input.
- User-uploaded artwork does **not** call `POST /api/generate` and triggers **no** model or GPU work.
- Invalid uploaded artwork preserves the previous valid deck texture.
- Returning to the generated decal works without regeneration.
- The remaining **prompt-adherence limitation is accepted and must remain documented**.

## 4. Generation budget — final record

**Final count: 26 total generations.**

| | |
|---|---|
| Research GPU budget | closed at **25 / 25** |
| Generation **26** | a **manual human-review run**, performed by Kylian himself during the final interface review |

**Generation 26 is outside the frozen research matrix.** It is **not** added to EXP-034, is **not**
registered in `experiments/registry.csv`, and is **not** treated as a new experiment — it produced
no research result and was not run under the pre-declared measurement conditions. Its only role is
as evidence that the interface behaved correctly, and its telemetry is quoted only for that.

**No further GPU generation is authorised for M7 closure.**

What its telemetry established (operation `cHWlV0J6Qgh2BKze`):

```
status completed · stage completed · current_step 30 · total_steps 30
denoising_fraction 1.0 · elapsed_seconds 40.83 · pipeline_loaded true
```

with **1** `POST /api/generate` and **48** `GET /api/generation-progress` polls in the API access
log — continuous delivery across the whole request. Kylian confirmed at this gate that the browser
displayed it.

## 5. Accepted limitations, carried into M8 and the report

These are approved **as limitations**, not as defects, and must remain documented:

1. **Cold model loading has no honest percentage.** ~30 s of model load exposes no progress
   signal, so the interface names the stage and offers no number.
2. **The ETA is approximate and mainly covers denoising.** It excludes loading, decoding, saving,
   transfer and texture application.
3. **Finalising may be visible only briefly** — about a second, the VAE decode plus PNG encode.
   **It must not be artificially delayed.**
4. **Prompt adherence can be weaker than style adherence.** Detailed prompt content may not
   survive strong style conditioning.
5. **The physical GPU margin remains approximately 200 MiB** (EXP-034 worst spare: 200.0 MiB).
   Not comfortable headroom.
6. **Only one API process and one worker are supported.** The busy lock is process-local and a
   second resident pipeline does not fit.

## 6. What this approval does NOT authorise

- **No push.** `main` remains ahead of `origin/main`.
- **The remote GitHub issue is not closed** and the project board is not moved — both are Kylian's,
  and `gh` is unavailable here.
- **M8 has not begun.**
- **No further GPU generation.**
