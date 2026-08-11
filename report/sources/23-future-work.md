# <span class="section-number">23</span> Future work

Ordered by what each would resolve. Every item names the limitation it addresses, so none of them is
a wish rather than a consequence.

## 23.1 Close the reproducibility defect

**Resolves:** §18.2.5 — training is not bit-reproducible from seed.

Seed the global generator alongside the explicit one, before adapter construction, with regression
tests in both directions. The runner fix is already authorised and written; what remains is the
expensive half — **re-running the affected comparisons**, because the fix is deliberately
forward-only and the existing evidence predates it.

Until that happens, the three production adapters remain artifacts rather than recipes, and the whole
restore-and-verify apparatus in §16.3 stays load-bearing.

## 23.2 Exercise the external backup

**Resolves:** §18.3.5 — the restore mechanism is validated, the external drive is not.

A restore from the external backup drive into a clean clone, with the same hash verification the
working-repository restore received. This is an afternoon's work and it closes the project's single
highest-impact residual risk: the loss of unregenerable artifacts.

## 23.3 Measure a second fine-tuning method

**Resolves:** §18.2.2 — LoRA is selected on feasibility, not superiority.

A minimal Textual Inversion [6] arm on the lead style, scored with the same rubric against the same
fixed-seed grid. It is the cheapest of the unmeasured four, and it would move DR-009 from a
feasibility claim to a measured comparison.

DreamBooth [5] and full fine-tuning would need more memory than this machine has, so they remain
future work **conditional on hardware** rather than on time.

## 23.4 Answer the image-count question properly

**Resolves:** §18.2.1 — RQ4's count half is inconclusive.

Re-run the size arms **matched on epochs rather than compute**, across more than one style, with set
sizes chosen to separate count from repetition. This is the one research question this project failed
to answer, and the reason it failed is a design decision rather than a measurement problem (§22.3).

## 23.5 Test the mitigation that was never tested

**Resolves:** §18.2.9 and the `retro-poster` partial pass.

Two things were never measured. A **crop pass** removing frames at the pixel level, which was
considered and rejected because it would have altered the dataset for one style only. And a
**caption A/B on `retro-poster` itself** — the existing A/B ran on the lead style, so the caption
strategy that was supposed to mitigate the poster problem was never tested against the poster
problem.

Either could move that style from partial pass to pass, and neither can be claimed without running.

## 23.6 Scale beyond one generation at a time

**Resolves:** §18.3.1 and §18.3.3 — a 2.4 % margin and a single-worker service.

With a ≥16 GB GPU: a second resident pipeline, or a queue with a separate worker process, becomes
possible. **Note what else that hardware would reopen** — SDXL [2] at its native resolution, which
this project's own rubric scored as the visual-quality winner and rejected only on memory, and the
multi-style adapter, which was viable and unselected.

This is the item that would most change the product, and it is entirely gated on hardware rather than
on any finding in this report.

## 23.7 Address the deployment questions this project did not

**Resolves:** §17.6.

A content-moderation position, provenance marking of generated output, a bias evaluation of generated
images rather than only of training data, and a licence position for commercial use given that the
base model's card states research intent [10].

These are not postponed features. They are questions a commercial deployment must answer before
launch, and this report deliberately does not answer them.

## 23.8 Product work that is genuinely optional

Listed last because none of it is required by any limitation: batch generation, a gallery of previous
results, more styles, user accounts, and export presets for real print production. Each is
straightforward and none of it would strengthen the research.

## 23.9 The one thing that should happen first

**§23.2, exercising the external backup**, is an afternoon and removes the risk of losing artifacts
that cannot be recreated. Everything else in this section can wait; that one is a race against a disk
failure.
