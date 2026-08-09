# Feature freeze

**In force from:** 2026-08-09, on M8 closure · **Until:** submission, 2026-08-17 06:00
**Authority:** the M8 plan, approved by Kylian Algoet · **Related:** DR-014, `docs/02-planning.md`

## Why now

The MVP is complete, validated and reproducible. Eight days remain, and every one of them is worth
more spent on the research report (M9) than on the code. The remaining risk to this project is no
longer "does it work" — it is "does a late change break something that was working".

The planning has said *"feature freeze 2026-08-15"* since Phase 0. This brings it forward to M8
closure because M8 finished ahead of that date, and a freeze that starts when the work is actually
done is worth more than one that starts on a calendar day.

## Allowed without a new decision

- **Blocking bug fixes** — a defect that prevents the application running, the tests passing, or
  the demo being given.
- **Documentation** — the report, corrections, clarifications, evidence indexing.
- **Test fixes**, and new tests that cover existing behaviour.
- **Demo preparation** — rehearsal, backup assets, slides, the screen recording.
- **Evidence organisation**, and traceability updates.

## Not allowed without an explicit new decision record

- Retraining any style, or changing any hyperparameter
- New styles, or reinstating the multi-style adapter
- Architecture changes
- UI redesign
- New generation features or conditioning methods
- Scheduler or sampler experiments
- Model replacement, or a different base model
- Output-format or geometry changes
- **Dependency upgrades**, including `npm audit fix` (see below)

## What a bug fix must satisfy

1. It fixes a **real, observed** defect — not a suspicion, and not a tidy-up.
2. It is the **smallest change** that fixes it.
3. Full validation passes afterwards: pytest, vitest, eslint, build, Playwright.
4. It gets a process-log entry saying what broke and why the fix is minimal.

If a "fix" needs a redesign, it is not a fix. Record it as a limitation instead — this project has
consistently scored better by documenting limitations than by hiding them.

## The six accepted limitations are NOT defects

The freeze does not reopen them, and M9 must present them as limitations rather than as unfinished
work. They were approved **as limitations** at the M7 gate:

1. Cold model loading has no honest percentage.
2. The ETA is approximate and covers measured denoising only.
3. "Finalising" may be visible only briefly, and must not be padded.
4. Prompt adherence can be weaker than style adherence.
5. The GPU margin is ~200 MiB, and is not comfortable headroom.
6. One API process, one worker, one generation at a time.

To which M8 adds two:

7. **`retro-poster` ships as a PARTIAL PASS** and warns on every request.
8. **The three production adapters cannot be regenerated (R14)** and must be restored from backup.

## Open items deliberately left open

Each was found during M8, is recorded, and is **not** being fixed under the freeze.

| item | why it stays open |
|---|---|
| 3 high-severity npm advisories (`brace-expansion`, `js-yaml`, `nanoid`) | Dev-tooling only, not in the shipped bundle, pre-existing. `npm audit fix` would move vite, eslint and typescript-eslint — the whole validated frontend — during a freeze. **Kylian's call.** |
| Transitive Python versions unpinned | The misleading comment is fixed; the versions are not constrained. Pinning is a dependency move needing a resolver dry-run and approval. |
| CI has never run | Committed, not pushed. The first GitHub Actions run is Kylian's decision. |
| No screen recording of the demo | Must be a recording of a real session or it does not exist. |
| `deliverables/.gitkeep` tracked while the directory is ignored | Cosmetic; removing a tracked file is not a bug fix. |

## What is frozen, concretely

Production generation settings and model behaviour, unchanged since M7:

- SD 1.5 pinned at `451f4fe1…`, three per-style LoRAs at weight **0.7**
- IP-Adapter `h94/IP-Adapter` @ `018e4027…`, default scale **0.55**, range 0.40–0.60
- 512×1536 direct, 30 steps, guidance 7.5, DPMSolverMultistep
- `full-surface` texture fit (DR-012), single-flight lock, one worker, lazy loading
- The three adapter files, by SHA-256

## After submission

The freeze ends at submission. The presentation on **2026-09-02** runs the **submitted** code —
nothing is changed between submission and presentation except demo rehearsal.
