# Session handoff

**Last updated:** 2026-08-14 (M10 — **structure approved, content corrected, NOT complete**; under
Opus 5)

## M10 STATUS — NOT COMPLETE. Do not record it as complete.

| | |
|---|---|
| deck content | **drafted and restructured; two claims corrected at the content review** |
| 15-slide structure | **approved by Kylian** |
| non-GPU validation | **passing** |
| **visual human gate** | **OPEN** |
| **rehearsal / criterion C** | **OPEN — no rehearsal has ever been run** |
| push | **NOT DONE** |

**M10 may only be called complete after the visual gate and a real rehearsal are actually passed.**

| item | state |
|---|---|
| authoritative slot | **20:00 TOTAL, live demo included** |
| deck | **15 slides** (was 26 — it overran by ~11 min and every check passed on it) |
| slide narration | **14:11** — ESTIMATE at 130 wpm, includes the 0:15 demo handoff |
| live demo | **4:00** target |
| combined / buffer | **18:11** / **1:49** |
| pages / geometry | **15 pages for 15 slides** · **960 × 540 pt = 16:9** |
| validator | **0 hard failures, 0 advisories** |
| fact locks | **32** |
| pytest | **527** |
| deck PDF | 1 052 201 B · `a11646b4…` |
| report PDF | **91 pages** · `3d439a5e…` |
| **issue** | **still open** — `gh` still absent |

### What Kylian has to do, in order

1. **Open `deliverables/DeckForge-AI-presentation.pdf` and review all 15 slides.** Every check is
   *structural*. Nothing here says the deck is legible or that the argument survives compression.
2. **Rehearse against a clock.** 14:11 is a word count at a *chosen* 130 wpm, not a measurement of
   how you speak. If it runs long, **re-cut from the notes**; the validator says when you are back
   inside the band.
3. Push, comment on and close the issue, move the board.

### ⚠️ The two corrections from the content review — do not undo either

**1. The VRAM figures on slide 3 must refer to ONE memory concept.** There are three, and only one
subtracts from the card:

| figure | counts | value |
|---|---|---:|
| **allocated** | live tensors in the PyTorch allocator | 5143.73 MiB |
| reserved | the allocator's cached pool | 6872.0 MiB |
| **device used** | context + reserved pool + display | **7987.5 MiB** |

`8187.5 − 7987.5 = 200.0` exactly. **`8187.5 − 5143.73 = 3043.77` is NOT the margin** — the deck
made that subtraction and it was caught by a human, not a check. `worst_device_used_mib` is now
fact-locked. **Do not put `peak_allocated_mib` next to `worst_spare_mib` as if they subtract.**

**2. Only Gate 1 was blinded.** `GATE-2-approval.md` records *"Unlike Gate 1, these sheets were
labelled"* and states the expectation effect. Approved wording: **"two human approval gates against
a rubric defined before the images were reviewed — the first blinded, the second labelled by
necessity."** **Do not restore "both gates scored blind"**, and do not swing the other way — Gate 1's
blinding was rigorous, with scores hashed before the map was opened.

**Note how the second one happened:** the 26-slide deck said *"blinding at the first gate"* and was
**correct**. The merge lost the qualifier. **Compression is where a qualified claim loses its
qualifier**, and the validator did not catch it because it checks the claims it was told to check.

### ⚠️ Do not undo these

**1. Do not solve an overrun by speaking faster.** 26 minutes of notes into a 15-minute slot needs
~220 wpm. That was rejected in DR-017 with its arithmetic.

**2. Do not trade a bounded claim for time.** `validate_slides.py` enforces the concessions on the
`limits`, `reproducibility`, `base-model` and `lora` slides, and the merged `limits` slide carries
**all three** bounds its three predecessor slides carried — retro-poster **partial pass**, image
count **inconclusive**, **no second independent human rater**.

**3. The narration band is hard in BOTH directions** (**825–855 s**, minimum buffer **1:45**). Under
the minimum means a note was gutted rather than cut. **Do not widen the band to fit the notes** —
that is the check doing its job. It was tightened once, at the content review, and the minute came
out of notes whose reasoning `jury-questions.md` already carries; `words_per_minute` stayed at 130.

**4. The demo is never counted as zero.** Its note is directions, so the slide is excluded from the
word count and the handoff (0:15) and demo (4:00) are declared costs in `deck.yaml`.

**5. Do not add `slides/facts.yaml`.** The deck holds no facts of its own; values resolve from
`report/facts.yaml`, so a number corrected in the report is corrected on the slide by the same edit.

**6. Everything cut is in `docs/presentation/jury-questions.md`**, structured for 30–60-second
answers with evidence paths. **Nothing was deleted.** Do not re-add it to a slide.

### The finding worth presenting, not just fixing

**Every structural check passed on a deck that did not fit.** 26 pages for 26 slides, 0 failures, 0
advisories, all fact locks green — and it overran by ~11 minutes. The checks were sound; **the
binding constraint was absent from the repository, so nothing could fail on it.**

Fourth instance of one pattern, and the first where the missing check was a *requirement* rather
than a *method*: M8's hash that only ran on its author's machine · M9's presentation-level
bibliography defect · M10's stale PDF that looked like success in `git status` · this.

It also showed DR-016's `core`/`supporting` tiering was **inadequate on its own**: only 4 of 26
slides were cuttable, saving ~4 min against an ~11 min overrun. **Tiering absorbs variation; it does
not absorb being wrong about the budget.**

### A defect the budgets could not see

The `limits` slide was authored with two-column markup and declared `bullets`. That grid is scoped
to `.slide--split`, so it was valid HTML, passed every budget, produced one PDF page — and would
have rendered with its evidence figure stacked under the text. `check_layout_markup` now fails a
build whose markup and declared layout disagree.

### Still OPEN from earlier in the day

**One report build came out 800 KB short at the same 91 pages and passed every check.** Did not
recur in 14 attempts; cause unknown. **The report build cannot detect the loss of 800 KB of
content.** No guard added — a threshold from one unreproduced observation is guesswork, and it means
editing `build_report.py` under the freeze. **Kylian's call; the risk is live.**

### Rebuilding

```
python scripts/validate_slides.py           # 0 hard failures expected
python scripts/build_slides.py --strict     # 15/15; Chrome is a prerequisite (DR-016)
python scripts/build_report.py --strict     # rebuild the report too - shared facts.yaml
python scripts/report_facts.py --check      # 31 locks
```

**Rebuilding changes every PDF's SHA-256** — hash *after* the final build, before `git add`, and
update the digests in `docs/evidence/M10/timing-restructure.md` and this file.

---

## Prior state — M10 first build (26 slides), superseded above

**The 26-slide deck did not fit the slot.** Its build record is
`docs/evidence/M10/build-record.md`, marked superseded in part. The two findings it records — the
stale PDF and the short report build — still stand and are carried above.

| item | state |
|---|---|
| slide sources | **26 of 26 authored** |
| validator | **0 hard failures, 0 advisories** |
| deck PDF | **committed** — `deliverables/DeckForge-AI-presentation.pdf`, 1 313 731 B, `42c5e8e2…` |
| notes handout | **committed** — `DeckForge-AI-presentation-notes.pdf`, 380 486 B, `71442da2…` |
| report PDF | **REBUILT and superseded** — 2 769 385 B, `73f57415…`, **91 pages** (was 90) |
| pages / geometry | **26 pages for 26 slides** · **960 × 540 pt = 16:9** |
| fact locks | **31** resolve |
| pytest | **518** (489 pre-existing + 29 slide-source tests) |
| **human visual gate** | **NOT HELD — this is the blocker** |
| **presentation duration** | **UNKNOWN — not recorded anywhere in this repository** |
| push | **NOT DONE** — 6 commits ahead of `origin/main` |
| **GitHub issue #10** | **still open** — `gh` still absent |

### What Kylian has to do, in order

1. **Open `deliverables/DeckForge-AI-presentation.pdf` and review all 26 slides.** Every check that
   has run is *structural*. Nothing in this repository says the deck is legible, well designed, or
   that its argument survives compression onto a slide. **M9's bibliography defect is the precedent:
   a source-level validator structurally cannot see a presentation-level fault.**
2. **Supply the real presentation duration** from the assessment material or the programme. It is
   **not recorded anywhere here** — searched twice. Until then the 26-slide length is *provisional*.
3. Decide the open report-build guard (see below).
4. Push, comment on and close **issue #10**, move the board.

### ⚠️ Do not undo these

**1. The deck holds no facts of its own.** Values resolve from `report/facts.yaml`, so a number
corrected in the report is corrected on the slide by the same edit. **Do not add `slides/facts.yaml`.**

**2. The text budgets and the page-count equality are HARD failures, not warnings.** A slide is a
fixed 190.5 mm box with `overflow: hidden`, so over-full content is **clipped silently**. **Do not
raise a budget to make a slide fit** — cut the slide or move the words into the speaker note.

**3. `tier` is why the deck can be shortened without lying.** A `supporting` slide folds into the
adjacent `core` slide's speaker note; it is never deleted. But only **4 of 26** are `supporting`, so
this absorbs a modest overrun, not a large one. **If the real duration is 15 or 20 minutes the deck
needs restructuring, not trimming.**

**4. ~30 minutes is an ESTIMATE, never a rehearsal time.** 26.4 min of slides (note word counts at
130 wpm) + a 4-minute demo target. **No rehearsal has been run.** Do not report it as measured.

**5. Slide 17's evaluation concession must stay**: one human approver, AI-assisted visual analysis,
**no second independent human rater**, so no inter-rater agreement can be reported. Same for slide
24's five refused conclusions.

### Two defects M10 found — do not re-discover these

**1. The committed deck PDF did not match its own sources.** Built 05:00:44 on 2026-08-11; the CSS
and one slide were edited at 05:03:57 and it was never rebuilt. **1 097 724 bytes on disk against
1 313 730 rebuilt — about 20 % of the deliverable was missing**, and nothing reported it. In
`git status` it looked exactly like success. Third instance of one class: M8's hash that only ever
passed locally, M9's bibliography defect, M10's stale artifact.

**2. OPEN — one report build came out 800 KB short and passed every check.** 1 968 295 bytes against
2 769 385 for the same sources, **same 91 pages**, structural check fine. **Did not recur in 14
attempts; cause unknown** (the file was overwritten before it could be examined). What it proves is
not in doubt: **the report build cannot detect the loss of 800 KB of content**, so a report with
missing figures would ship looking correct. **No guard was added on purpose** — a threshold from one
unreproduced observation is guesswork, and it means editing `build_report.py` under the freeze.
**Kylian's call; the risk is live until he takes it.**

### Writing DR-016 changed the report — this is the fact lock working

`decision_record_count` globs `docs/decisions/DR-*.md`, so creating DR-016 moved it 15 → 16 and
**failed the deck build**. `report/facts.yaml` and Appendix B were updated and the report rebuilt,
taking it **90 → 91 pages**, which invalidated the typed literal "90-page report" on slide 26 and in
the traceability matrix. **The page count is NOT fact-locked and cannot be** — it exists only after
Chrome paginates — so it stands as a live drift risk in DR-016. Dated historical records that say 90
pages are correct for their date and **were not rewritten**.

Requirement 13's rows now read **"built, NOT yet gated"**. **Do not upgrade them to "met"** before
the visual gate.

### A wrong inference caught inside the session — keep the correction

Repeat builds were first recorded as "byte-identical" from their **matching sizes alone**. Hashing
three returned **three different digests at the same length**, confirming DR-015's timestamp
explanation. **Equal length is not equal content.**

### There is no M9 entry in `docs/ai-usage.md`

Stated as a gap rather than reconstructed. That log exists to record the human/AI boundary, and
writing one three days later from commits would be exactly the plausible-but-unwitnessed account it
guards against. **Kylian should write it, or it stays absent and is reported as absent.**

### Rebuilding the deck

```
python scripts/validate_slides.py           # 0 hard failures expected
python scripts/build_slides.py --strict     # 26/26; Chrome is a prerequisite (DR-016)
python scripts/build_report.py --strict     # rebuild the report too - they share facts.yaml
python scripts/report_facts.py --check      # 31 locks
```

**Rebuilding changes every PDF's SHA-256** (Chrome embeds a timestamp), so hash *after* the final
build and before `git add`, and update the digests recorded in `docs/evidence/M10/build-record.md`,
DR-016 and this file.

### M10 commits

```
3e5a9b3 build(slides): add the defence deck build pipeline and its validator
f531abd docs(slides): author the 26 defence slides and their speaker notes
126bf89 docs(decisions): record DR-016 and track the presentation PDFs
6d21600 docs(report): count DR-016 and rescope the requirement 13 claims
1398042 docs(m10): add the presentation PDFs and the M10 build record
b63ecbc docs(m10): update the process, planning, traceability and AI-usage records
```

---

## Prior state — M9, superseded above

**Last updated:** 2026-08-11 (M9 — research report **finalised and PUSHED**; issue and board remain
open and are Kylian's, under Opus 5)

> **Note added 2026-08-14:** M9's report artifact figures below (90 pages, `5c394e7a…`) are the M9
> record and are **no longer the file on disk** — see the M10 section above.

## M9: report finalised and pushed. TWO REMOTE ITEMS REMAIN, AND THEY ARE KYLIAN'S

| item | state |
|---|---|
| report sources | **26 of 26 mandated sections** |
| final PDF | **committed and pushed** — `deliverables/DeckForge-AI-research-report.pdf` |
| pages / bytes / sha256 | **90** · **2 756 980** · `5c394e7a111374d3c1e7aa0d178db25144f22e1cc5736477b985095710ca8a93` |
| built from | `42b0ca9` · committed in `ba5d4c7` |
| push | **DONE** — `a2d70c1..ba5d4c7`, `main` == `origin/main`, 0 ahead / 0 behind |
| validator | all hard checks pass · 29 fact locks · 20 references, contiguous, no orphans |
| pytest | **489** |
| **GitHub issue #10** | **NOT CLOSED — `gh` is absent from this machine** |
| **project board** | **NOT MOVED — same reason** |
| **M10** | **NOT STARTED** |

### Why the issue and board are still open

`gh` is not on PATH and is not installed anywhere standard (checked: PATH, `Program Files\GitHub
CLI`, `AppData\Local\GitHubCLI`, chocolatey, scoop). Installing it would be a tooling change under
an active feature freeze, and closing a public issue is Kylian's action in any case. **The session
did not claim these were done.**

Everything else in the M9 finalisation sequence completed and is verified.

### What Kylian still has to do

1. Comment on **issue #10** with the M9 completion summary and close it.
2. Move the M9 item on the public project board to **Done**.
3. Confirm the public planning state reflects M9 complete and M10 not started.

### ⚠️ Three corrections from the final gates that must not be undone

**1. The AI-scoring disclosure.** The report had claimed every rubric score was the student's. The
preserved gate artifacts say otherwise: Gate 1 records *"ChatGPT visual review with Kylian present"*,
Gate 2 records *"Visual-analysis assistance: ChatGPT"* with Kylian as final human approver. Approved
wording, used in nine places:

> Visual evaluation was AI-assisted: ChatGPT contributed visual analysis and proposed scoring at the
> review gates, while Kylian Algoet reviewed and approved the recorded scores and retained final
> authority over every production selection and research conclusion.

**2. GPU execution and validation authority.** Do not restore *"No generation was ever run by an
assistant"* or *"No assistant validated its own results"* — both were more absolute than the
evidence supports. The approved formulations:

> Every GPU generation was explicitly authorised by Kylian Algoet; no AI assistant had authority to
> initiate GPU inference without that approval.

> No AI assistant had final validation or decision authority over its own work; AI-assisted visual
> evaluation was reviewed and approved by Kylian Algoet.

**Do not make the opposite error either** — Kylian did review and approve the scores, and that must
stay stated.

**3. The RQ taxonomy.** **Eight answered within their stated scope** (RQ2, RQ3, RQ5, RQ6, RQ8, RQ9,
RQ10, RQ12); **four bounded** (RQ1, RQ4, RQ7, RQ11); **RQ4's image-count component explicitly
inconclusive**. RQ1 is bounded because the question asks *feasible and most effective* and "most
effective" was never established. **Do not report ten of twelve.**

Unchanged and separately evidenced: generation total **27**, offline indicators populated no rubric
cell and selected no checkpoint, `retro-poster` remains a **PARTIAL PASS**, training is not
reproducible from seed while inference is.

### The defect the visual gate caught that the validator could not

The bibliography printed `[1]` again at the start of each of its four subsections, so reference 10
rendered as `[1]`. The validator checks the Markdown source, where numbering was correct all along;
the fault was in the CSS that replaced the list markers. **A source-level check cannot see a
presentation-level defect** — which is why the rendered-page gate exists.

### 90 pages is accepted — do not compress

No hard page limit exists in the assignment material, all 26 sections are authored, and evidence
completeness takes precedence. A genuine repetition pass moved the count by **under one page**: the
cause is structural, 26 sections each starting a new page costing roughly 13.

### Rebuilding the report

```
python scripts/build_report.py --strict     # 26/26 required; Chrome is a prerequisite (DR-015)
python scripts/validate_report.py           # hard checks vs advisories
python scripts/report_facts.py --check      # 29 fact locks against their evidence
```

The PDF reproduces in **content** from tracked sources but **not byte-for-byte** — Chrome embeds a
timestamp and its version. The recorded SHA-256 identifies the submitted artifact only.

### Next milestone

**M10 — presentation, speaker notes, jury preparation. NOT STARTED.** It inherits requirement 13 as
the one mandatory requirement still outstanding, and a report that states so.

---

## Prior state — M8, superseded above

## M8: CI GREEN — waiting only on formal closure

**All three GitHub Actions jobs pass.** Run #9 (`e9c9fb4`) — Status **Success**, 18m 56s: pytest
**PASS** 2m 30s · vitest/eslint/build **PASS** 1m 0s with 183/183 · playwright **PASS** 18m 50s
(E2E step 14m 45s), no failure artifact. Run #8 (`d29fba8`) is green too. Acceptance criterion 1 is
now evidenced **remotely** as well as locally.

**What remains is Kylian's, and only his:**

| item | state |
|---|---|
| the push | **done** — `main` == `origin/main` |
| CI | **green**, runs #8 and #9 |
| GitHub issue #9 | **not closed** |
| the project board | **not moved** |
| **M9** | **NOT STARTED — do not begin until Kylian closes M8** |

### Read these three qualifications before quoting the green

1. **Run #8 passed under the OLD budgets** (60 s / 10 s, retries on). So run #9's green **cannot be
   attributed to the budget change alone** — the stall is intermittent. The budget removes a known
   failure mode; it is not proven to be why CI is green.
2. **The per-scenario retry counts could not be read** from the collapsed E2E log. Whether anything
   passed only on retry is **unknown, not zero**. The missing artifact does not settle it: that
   upload is `if: failure()`.
3. **A green run under `retries: 2` and a 180 s CI budget is weaker than a first-attempt green under
   60 s.** Say so in the report.

**What stands without any accommodation:** the camera scenario **passed on CI on its first attempt,
in 40.2 s, in run #7 — before any budget was raised.**

### The lesson this milestone produced twice — strong D5/D6 material

**A green local sweep is not evidence about CI.** The first fix passed pytest, vitest, eslint,
typecheck, build, the bundle gate and all 38 Playwright scenarios locally, five times over, and
still failed remotely. And `git status -sb` showing no `[ahead]` marker means commits were **pushed,
not that they passed** — a resumed session made exactly that inference on 2026-08-10 and started M9
on the strength of it. M8 had already found the same class of defect once, in a dataset integrity
hash that had only ever passed on its author's machine.

### The camera scenario, for the report

300 s timeout → 60 s timeout → 60 s timeout → **40.2 s pass**. Two rewrites of the *measurement*,
never of the application. Two defects found in my own work on the way: an equality rule for a camera
that damping means never comes exactly to rest, and a drift tolerance wide enough to swallow an
entire change of viewpoint — the second caught by a unit test before it reached CI.

### Historical: the runs that were red

- **CI is NOT green.** Run #4 (`68d1bf2`): pytest **PASS**, vitest/eslint/build **PASS**, Playwright
  **37 passed, 1 failed** — the camera-preservation scenario timed out after 300 000 ms.
  Run #5 (`316b2cd`, the first fix): pytest **PASS**, vitest/eslint/build **PASS**, Playwright
  **35 passed, 3 failed**.
  Run #6 (`f409b65`, the second fix): pytest **PASS**, vitest/eslint/build **PASS**, Playwright
  **32 passed, 6 failed** — and a *different* six.

### Run #7: the camera fix WORKS on CI. Do not reopen it.

`b09035a` → **36 passed, 1 flaky, 1 failed.** `replacing the decal does not reset the camera`
**passed in 40.2 s on its first attempt, no retry.** The assigned defect is fixed and proven
remotely. Leave it alone.

The remaining red is **`a completed generation shows the image, the duration and the metadata`** —
pre-existing, untouched by this work, and it passed in 11.4 s in run #5. It failed all three
attempts (2.3 m, 2.4 m, 2.0 m), so retries correctly did **not** mask it, while
`offers a PNG download` failed once and passed on retry #1 in 9.1 s and was reported as flaky.

**The runner stalls in multi-minute windows.** Three neighbours of the failing test share its setup
exactly (`generateDelayMs: 300`) and took **5.6 s, 8.0 s and 9.1 s** in the same run, with the same
code path taking over two minutes in between. Playwright retries immediately, so all three attempts
landed inside one stall; the other test's retry fell outside it. **Retries cannot help a stall that
outlasts a retry cycle** — do not just raise the retry count.

**The per-test budget decision has since been taken**, on measured evidence rather than guesswork.
The trace of run #7's last failing attempt (`docs/evidence/M8/ci/runner-stall-trace.md`) recorded
`fill` **21.58 s**, `click` **37.15 s** — 59.1 s of a 60 s budget gone before the assertion under
test began — and a single mocked response taking **12.78 s** to fulfil against a 10 s `expect`
timeout. The application was ruled out: it never received a response to act on, and the DOM snapshot
shows it correctly reporting the only state it had been told about.

CI budgets are now **`timeout: 180 s`, `expect.timeout: 45 s`**; **local stays 60 s / 10 s**, because
the suite runs in ~1.2 minutes here and a local scenario needing more than 60 s has found something.
The `e2e` job guard moved 45 → 60 minutes.

**Do not raise the LOCAL budgets to match.** That would delete the suite's only performance signal.
**Do not describe the CI budgets as a fix** — the stall is real and unexplained; a budget lets a slow
environment finish, and it means CI can no longer detect a genuine performance regression.

### The earlier finding: the runner, not the camera test

Run #6 settled it. The camera scenario timed out at its **third** probe, the cheap 7-frame one,
while the expensive 94-frame probe before it completed and passed its drift check. The measurement
was no longer the bottleneck. Meanwhile five *unrelated* scenarios failed waiting for a **mocked**
4-second response, and the subsets barely overlap between runs:

| scenario | run #5 | run #6 |
|---|---|---|
| `?review=1` restores both review tools | 2.6 s pass | **56.8 s** pass |
| 409 is presented as busy | **FAIL** | 6.4 s pass |
| offers a PNG download | 20.9 s pass | **FAIL** |

1 failure in run #4, 3 in #5, 6 in #6, with a **22x** swing on identical code. **Do not spend
another round making the camera test cheaper** — that cannot turn CI green, and two rounds already
proved it.

**Kylian chose retries** (2026-08-10), over a larger suite timeout and over disabling damping in
E2E builds. `retries: process.env.CI ? 2 : 0`; locally still 0. The `e2e` job's `timeout-minutes`
went 30 → 45 so a retrying run can finish and report — that is the job's wall-clock guard, and no
per-test budget was touched.

**Report a green run under retries honestly:** it means every scenario passed *within three
attempts*. Quote the retry counts. And if scenarios fail all three attempts, retries were the wrong
remedy and the environment or the timeout has to change after all.

**A green local sweep is not evidence about CI, and this milestone has now proved that twice.**
Attempt 1 passed pytest, vitest, eslint, typecheck, build, the bundle gate and all 38 Playwright
scenarios locally, five times over, and still failed remotely. Do not report a local pass as a CI
pass.

**A local pass is not a remote pass**, and this project has already been bitten by exactly that
distinction once: M8's own clean-clone test found an integrity hash that had only ever passed on
its author's machine.

### Current position

The failing scenario has been rewritten and every local gate is green (see below), but **the remote
run has not happened yet**. M8 closes when all three CI jobs are green — not before.

| what | state |
|---|---|
| the CI fix | committed locally |
| the push | **do it, then wait for Actions** |
| GitHub issue #9 | **not closed** — Kylian's |
| the project board | **not moved** — Kylian's |
| **M9** | **NOT STARTED, and must not start until CI is green and M8 is formally closed** |

### The fix, in one paragraph

`replacing the decal does not reset the camera` answered a structural question photographically: it
settled the WebGL canvas four times and compared screenshots, which on a GPU-less runner is
software-rasterised and unaffordable. It now reads the camera position, quaternion and orbit target
directly, through read-only instrumentation gated on `__DECKFORGE_E2E__` — a Vite `define` that is
literally `false` in ordinary builds, so the probe is tree-shaken out entirely. `VITE_E2E=1` is set
only by the Playwright `webServer`. **No application behaviour changed.** Full record:
`docs/evidence/M8/ci/camera-preservation-fix.md`.

**Do not "simplify" the gate to `import.meta.env.VITE_E2E`.** Only a `define` is substituted
literally, and only a literal makes the branch dead code; an env lookup leaves the handle name in
the shipped bundle. `npm run verify:no-e2e-handle` asserts this after every build and runs in CI.

### Three things about the camera measurement that must not be undone

1. **Wait in FRAMES, never in milliseconds.** OrbitControls damping advances only when a frame
   renders, so a wall-clock rule is a bet on the frame rate — and that bet is what failed on the
   runner. Attempt 1 polled every 100 ms; attempt 2 counts rendered frames.
2. **Keep the whole loop inside one `page.evaluate`.** Attempt 1 cost ~120 Node↔browser round trips
   per phase. On a runner where the WebGL scenarios run ~15x slower, that alone blew the 60 s budget.
3. **Keep the tolerance derived, not hard-coded.** The probe measures the camera's residual drift on
   the machine running the test and derives the tolerance as `max(drift x 20, 1e-3)`. Drift above
   `MAX_RESIDUAL_DRIFT` fails as **UNMEASURED**, not as a camera-preservation failure.

**Do not raise `MAX_RESIDUAL_DRIFT` back to 0.05.** At 0.05 the worst permitted tolerance is exactly
`DISTINCT_VIEWPOINT` (1.0), wide enough to swallow a whole change of viewpoint and make the
comparison decorative. A vitest case asserts
`toleranceForDrift(MAX_RESIDUAL_DRIFT) < DISTINCT_VIEWPOINT`; it caught this before the commit.

### Local gates, measured 2026-08-10 (attempt 2)

**473 pytest** · **183 vitest** · **38 Playwright** · eslint clean · `typecheck:e2e` clean ·
production build succeeds · production bundle contains no E2E handle (and the guard was proven to
detect one in a `VITE_E2E=1` build). Camera scenario ~4 s, was ~138 s. Whole E2E suite 1.2 min.
**All of this was also true of attempt 1, which failed on CI. Treat it as necessary, not
sufficient.**

### The accidental M9 start on 2026-08-10 — nothing to clean up

A resumed session misread this file and began M9 before being stopped. **No repository file was
created or modified**, no commit was made, and the working tree stayed clean. Two findings are worth
keeping for when M9 legitimately starts: pandoc, pdflatex, xelatex, tectonic, wkhtmltopdf and
soffice are all **absent** from this machine, while `markdown-it-py` 4.2.0, Jinja2 3.1.6 and
Pygments 2.20.0 are already in the venv and headless Chrome `--print-to-pdf` works — so a report
build with **zero new dependencies** is feasible under the freeze.

---

## The 2026-08-09 close, superseded above

*Kept because its warnings still apply. Its status line does not.* All six acceptance criteria on
issue #9 are met **locally**. Index: `docs/evidence/M8/README.md`.

| # | criterion | evidence |
|---:|---|---|
| 1 | Backend, frontend and E2E suites pass | `M8/baseline/test-baseline.md`, `M8/tests/playwright-e2e-report.md` |
| 2 | Upload-security tests pass | `M8/security/upload-security-matrix.md` |
| 3 | Deployment decision recorded | **DR-014** |
| 4 | Clean-clone test with real output | `M8/clean-clone/log.md`, `real-output.md` |
| 5 | Timed demo script | `docs/presentation/demo-script.md` |
| 6 | Backup demo plan | `docs/presentation/demo-backup-plan.md` |

~~**M8 is closed LOCALLY ONLY.** Three things remain Kylian's and are **not** done:~~

1. ~~**the push** — verify with `git status -sb`;~~ — **done.** The push happened, and the CI run it
   triggered is what reopened the milestone. Note the trap this line set: `git status -sb` tells you
   whether commits were pushed, **not** whether they passed.
2. **the GitHub issue #9** — still not closed (`gh` unavailable here), and it must not be closed
   while CI is red.
3. **the project board** — still not moved.

**M9 (research report) has not begun**, and must not begin before M8 is formally closed.

### ⚠️ Eight things the next session must not do

1. **Do not push, close issue #9, or move the board** without Kylian saying so.
2. **The FEATURE FREEZE is in force** (`docs/process/feature-freeze.md`). Blocking bug fixes,
   documentation, tests and demo prep only. No retraining, new styles, UI redesign, new features,
   or dependency upgrades without a new decision record.
3. **Do not run GPU inference.** The total is **27** and no further generation is authorised.
4. **Do not report the generation count as 25.** It is 25 research + 1 M7 human review + 1 M8
   deployment validation = **27**. The M8 run has no `EXP-###` and is not in the registry.
5. **Do not merge `DATASET_V1_SHA256` and `DATASET_V1_CONTENT_SHA256`.** They answer different
   questions and a test asserts they stay separate — see below.
6. **Do not claim CI passes.** The workflow is committed and **has never run**.
7. **Do not run `npm audit fix`.** Three high-severity advisories exist; all are pre-existing,
   dev-tooling only, and fixing them moves vite/eslint/typescript-eslint under a freeze.
8. **Do not quote the byte-identical reproduction as contradicting R14.** R14 is about *training*;
   the M8 result is about *inference*. Different halves of the pipeline.

### The two dataset constants — read before touching either

M8's clean-clone test found that the frozen dataset hash **failed on every clean clone**:
`DATASET_V1_SHA256` was taken from a CRLF working copy while Git stores LF, so an integrity control
had only ever passed on the machine that wrote it.

| constant | answers | value | status |
|---|---|---|---|
| `DATASET_V1_SHA256` | which dataset configuration was M6 run against? | `cd18cbb0…` | **unchanged** — feeds `kit_fingerprint()` (`fc11d828…`) and every run's `dataset_version` |
| `DATASET_V1_CONTENT_SHA256` | has the content been modified? | `b38996ae…` | the integrity check, normalised to LF |

Repointing the first would move a frozen fingerprint M6 evidence cites as unchanged. **Do not
"simplify" this into one constant.**

### Measured position at close

- **473 pytest**, **169 vitest**, **37 Playwright E2E**, eslint clean, build succeeds. **No Python
  linter is installed.** A clean clone runs **468 passed / 5 skipped** (pre-existing conditional
  skips for git-ignored assets; 468 + 5 = 473).
- **The clean clone reproduced M7's Phase A output byte-for-byte** — sha256 `46bbf160e427…`,
  1 089 939 bytes, fresh environment, three days later.
- `peak_allocated_mb` **5143.73** — byte-identical across EXP-019b, EXP-034 and the M8 run.
- The M8 run's `spare_device_mb` **218.0 is the prompt-only figure** and does **not** supersede the
  **200.0 MiB** reference-conditioned production ceiling.
- The three production checkpoints re-verified on disk: 3/3 match, 6 414 480 bytes each.
- Clean-clone directory **deleted**; regenerable in ~10 minutes from `docs/deployment/runbook.md`.

### Five defects M8 found — do not "re-discover" these

1. **The frozen dataset hash only ever passed locally** (fixed, above).
2. **`.env.example` documented five variables nothing reads**, two implying upload security rules
   were configurable. Fixed; a pytest now derives the permitted set from `config.py` by AST.
3. **The audited Node version was stale** — v20.18.0 recorded, **v24.18.0** actual. Corrected;
   the `vite.config.ts` jsdom comment was rewritten. **The jsdom pin itself was not moved.**
4. **`apps/api/requirements.txt` claimed a pin it did not make** — four "pinned" lines were
   comments. Comment fixed; **versions deliberately not changed** under the freeze.
5. **`uvicorn --workers 1` starts TWO processes** — a supervisor and a worker. `/api/health`
   reports the *worker's* pid, not the one `start-demo.ps1` launched, and stopping only the
   recorded pid strands the worker on port 8000. `stop-demo.ps1` stops the tree.

### Start commands

```powershell
.\scripts\preflight.ps1      # 10 checks incl. the three adapter hashes
.\scripts\start-demo.ps1     # API (one worker) + frontend, prints the URL
.\scripts\stop-demo.ps1      # stops only what it started, verifies ports
```

Full procedure: `docs/deployment/runbook.md`. `?review=1` still restores the two review tools.

### Open items, all deliberate

| item | why |
|---|---|
| CI has never run | committed, not pushed — Kylian's call |
| 3 npm advisories | dev-tooling only, pre-existing, freeze |
| Transitive Python versions unpinned | comment fixed; pinning is a dependency move |
| No screen recording for the demo | must be a real session or it does not exist |
| External weight backup not exercised | the clean clone restored from the working repo; the *mechanism* is validated, the **external drive is not** |
| Pre-warm before the presentation? | costs generation 28 — Kylian's call |

### Next milestone

**M9 — research report. NOT STARTED.** It inherits: 473/169/37 passing, DR-001…DR-014, EXP-001…
EXP-035, a **27** generation total, eight accepted limitations, and five M8 defect stories that are
strong D5/D6 material — particularly the integrity check that had only ever passed on its author's
machine.

---

## Prior state — M7 (Prototype 5 — integrated MVP): COMPLETE 2026-08-07

*Historical section, superseded by the M8 section above. Its "nine things the next session
must not do" were written for the M8 session and have been acted on: M8 is complete, the
generation question was resolved at the M8 gate (total now **27**), and the Playwright layer
it lists as not existing now exists with 37 scenarios.*


**Approved by Kylian Algoet at the final human visual gate on 2026-08-07 — 12 of 12 manual
acceptance items PASS.** Record: `docs/evidence/prototype-5/FINAL-GATE-approval.md`.

Approved: the redesigned production interface · the real generation-progress and ETA
implementation (DR-013) · `Upload your own decal` as a production feature · `full-surface` as the
production texture-fit default (DR-012, re-confirmed).

**M7 is closed LOCALLY ONLY.** Four things remain Kylian's and are **not** done:

1. **the push** — `main` is ahead of `origin/main`;
2. **the GitHub issue** — not closed (`gh` is unavailable here);
3. **the project board** — not moved;
4. **M8** — not begun.

### ⚠️ Nine things the next session must not do

1. **Do not push, close the remote issue, move the board, or start M8** without Kylian saying so.
   M7 being complete does not authorise any of them.
2. **Do not run GPU inference.** The budget is closed at **26** and no further generation is
   authorised. Every generation past 25 is Kylian's own decision, not an assistant's.
3. **Do not add generation 26 to EXP-034 or to `experiments/registry.csv`.** It was a manual
   human-review run outside the frozen research matrix, made under different conditions. Adding it
   would contaminate a frozen matrix; quietly reporting the total as 25 would be worse.
4. **Do not add a fake or weighted progress percentage.** Only denoising has a real denominator.
   Loading, decoding and saving publish a stage name and a **null** estimate, a test enumerates
   every non-denoising stage to prove it, and **100 % waits for the PNG to decode in the browser**.
   Do not replace the deadline callback — `compose_step_callbacks` threads progress through it, and
   passing a progress callback directly would silently remove the abort behind a truthful 504.
5. **Do not artificially delay "Finalising the decal…".** It is ~1 s and Kylian approved it that
   way. Padding a finished result to make a label linger is the dishonesty the feature exists to
   avoid.
6. **Do not describe the margin as 202 MiB.** EXP-034 measured **200.0 MiB** worst spare under real
   serving. It is the operative production ceiling and is **not** comfortable headroom.
7. **Do not add a second worker, Gunicorn, `WEB_CONCURRENCY > 1`, or `--reload` for real work.**
   The busy lock is process-local and a second resident pipeline does not fit.
8. **Do not "simplify" the prompt-only path by dropping the placeholder.** Diffusers 0.39.0 raises
   if IP-Adapter is resident and no image is passed; EXP-035 proved the placeholder inert at 0.0.
9. **Do not weaken the checkpoint integrity gate**, and never prove it by damaging a real adapter —
   R14 means they cannot be regenerated. Phase B used a corrupted *copy*.

### The prompt-adherence limitation — accepted, must remain documented

A prompt for *"A futuristic city skyline with a skateboarder jumping over neon buildings"* produced
a **clearly `minimal-geometric` and usable** deck graphic in which **the skyline and the
skateboarder were not clearly represented**. Strong style conditioning dominated detailed content.

Consistent with M6's measured drop in prompt adherence at step 600 — **not** a frontend failure.
**Do not** hide it, retrain, change the LoRA weight default, change prompt assembly, or add
automatic prompt rewriting.

### Accepted limitations carried into M8

1. Cold model loading has **no honest percentage**.
2. The ETA is **approximate and mainly covers denoising**.
3. **Finalising may be visible only briefly** and must not be delayed.
4. **Prompt adherence can be weaker than style adherence.**
5. The physical GPU margin is **~200 MiB**.
6. **One API process and one worker only.**

### Measured position at close

- **406 pytest** and **165 vitest** pass; eslint clean; `npm run build` succeeds. **No Python
  linter is installed.**
- **Generation budget: 26 total.** Research budget closed at 25/25; #26 was Kylian's manual
  review run. **No generation was ever run by an assistant.**
- The three production checkpoints were re-hashed on disk at closure and **match**, 6 414 480
  bytes each.
- **EXP-034:** allocated after generation **3316.64 MiB in all 13 runs**, growth **0.00 MiB**; peak
  **5143.73 MiB**, byte-identical to M5's EXP-019b; **worst spare 200.0 MiB**.
- **EXP-035:** grey placeholder and real holdout artwork **byte-identical** at scale 0.0.
- **Phase A:** 6/6, 12–13 s resident (30.54 s first). **Phase B:** corrupted copy → 503, recovery →
  200 with no restart. **Phase C:** 504 after **14 of 30 steps**, lock released.
- **Both review servers were stopped cleanly** (API pid 25748, frontend pid 476); ports 8000 and
  5173 released; no duplicate uvicorn or vite process remained.

### Start commands, plus the review flag

```
.venv/Scripts/python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 1
cd apps/web && npm run dev            # http://localhost:5173
```

**`http://localhost:5173/?review=1`** restores the **two** review tools — the texture-fit selector
and the inverted-UV demonstration. Hidden from production but **not deleted**: the fit comparison
is the evidence behind DR-012. `VITE_REVIEW_MODE=1` does the same for a dev server.

**Load-from-disk is no longer a review tool.** It became the production feature *Upload your own
decal*; the review-only duplicate was removed.

### Regenerate the evidence

`scripts/measure_service_residency.py` (`--smoke`) · `scripts/validate_p5_api.py` (`--phases C`) ·
`scripts/measure_reference_neutralisation.py`. **All consume GPU budget — see item 2.**

### M7 commits, in order

```
6e53a67 feat(api): add the resident single-flight generation service
6d900ce docs(experiments): record EXP-034, the resident-service residency run
a2b9219 feat(web): add the generate flow and both deck texture-fit modes
a9f5749 test(api): validate prototype 5 end to end against a real uvicorn process
83e6280 feat(web): add a review-only control to load a decal from disk
ce90388 docs(process): record prototype 5 and stop at the review gate
0835c61 docs(process): record the prototype 5 commit hash in the session handoff
3b12188 feat(web): adopt full surface as the production texture-fit default
0c756e1 docs(process): record the m7 texture-fit gate decision
4107c6b docs(process): record the texture-fit gate commit hashes in the session handoff
ce9818d feat(api): expose read-only generation progress telemetry
acb5b36 feat(web): add the generation progress client, model and print panel
732e735 feat(web): rebuild the creation workspace and wire in live progress
1526714 test(web): cover generation progress and the polished production states
46f893d fix(web): correct three layout and language defects found in the browser
f38e41b docs(m7): record the interface pass, DR-013 and the walkthrough finding
b294d37 feat(web): add upload your own decal as a production feature
c471060 docs(m7): record the telemetry verification and the decal upload
```

Closure commits are appended by the closure session; verify the real list with
`git log --oneline origin/main..HEAD` rather than trusting this block.

### Next milestone

**M8 — testing, deployment and demo. NOT STARTED.** It inherits a single-process service by
design, the **~200 MiB** ceiling, `full-surface`, `retro-poster` as a named partial pass, the
prompt-adherence limitation, and a **Playwright E2E layer that does not exist yet**.

---

## Prior state — M6 (Prototype 4 — style learning): **COMPLETE**, both gates passed 2026-08-05

*Historical section. M6 was completed **and pushed**: `origin/main` reached `6d1b24b`. Any line
below claiming M6 is unpushed is stale and superseded by the M7 section above.*

**Both gates passed.** Kylian scored the labelled Gate-2 sheets (ChatGPT assisted the visual
analysis; he is the final approver), selected the production checkpoints, and finalised DR-010.
Records: `docs/evidence/prototype-4/GATE-2-approval.md` and `GATE-1-approval.md`.

### The production artifacts — preserve these files

| style | run | step | sha256 | outcome |
|---|---|---:|---|---|
| minimal-geometric | EXP-027 | **300** | `2d425838cce59adc5c12b894e29439b695b98b9e40ef5d7ae667bd5216cb96a8` | PASS |
| ukiyo-e | EXP-028 | **600** | `52381b6052ad71f165ed23425bfc4ea1ba794a3886948a741cea9cad3d81abfd` | PASS |
| retro-poster | EXP-029 | **300** | `70d2afbfb3c09aff6ba37e1f1cf82c02ad69b0269969ea7cdf43b0ead17ba8db` | PARTIAL PASS |

All in **git-ignored** `outputs/lora/<run-slug>/step00300|step00600/pytorch_lora_weights.safetensors`.
Each is 6 414 480 bytes, 256 tensors, 256 LoRA keys, **zero base-model keys**.

**These files are authoritative as FILES, by sha256 — not as a recipe.** Because of R14 they
cannot be regenerated from their seed. **Do not delete `outputs/lora/`, do not retrain, do not
"regenerate" them.** If they are lost, the production selection is lost with them.

**Default application LoRA weight: 0.7**, optional range 0.4–1.0. **Three separate per-style
adapters**, not the multi-style one.

### ⚠️ Seven things the next session must not do

1. **Do not retrain any style**, and do not change learning rate, rank/alpha, dataset, captions,
   resolution, optimizer or step count. No contingency is authorised; **both slots are unused.**
2. **Do not rerun or replace EXP-027…EXP-030** after the R14 seeding fix. The fix is
   **forward-only**; the M6 evidence predates it deliberately.
3. **Do not claim the M6 artifacts are bit-reproducible from seed.** They are not. The fix
   improves *future* reproducibility and changes nothing retroactively.
4. **Do not upgrade `retro-poster` to a full pass.** It is a **PARTIAL PASS** — H4 confirmed:
   pseudo-text, poster borders, framed composition, repeated layout motifs. It is also **not
   dropped**.
5. **Do not describe the multi-style adapter as a failed experiment.** It is **viable but not
   selected** — competitive at 512×512, no severe cross-style bleed; per-style adapters won on
   flexibility because each style needs a *different* checkpoint.
6. **Do not describe ~202 MiB as comfortable headroom**, and never silently reduce geometry.
7. **Do not push, and do not update the GitHub issue or board** — `gh` is unavailable and those
   browser actions are Kylian's.

### What Gate 2 decided, in one line each

- **RQ5:** three separate per-style adapters selected; multi-style viable, not selected.
- **H4:** **confirmed** for `retro-poster`.
- **H5:** **supported** — 0.7 is a compromise, **not a universal optimum**.
- **RQ4 image count:** **O5 inconclusive**, non-monotonic; no minimum count established.
- **Captions:** style-only, selected at Gate 1 from a blinded A/B.
- **DR-010:** **accepted**.

### The result worth remembering

**Two of the three selected checkpoints are step 300, not the 600 the runs trained to.** Prompt
adherence fell from 4 to 3 at step 600 for both `minimal-geometric` and `retro-poster` while
style consistency held at 5 — training longer made the style stronger and the model less
obedient. Only `ukiyo-e` improved. Checkpointing at 150/300/450/600 and letting a human choose
per style is what surfaced it.

### Measured position at close

- **10 of 12** training runs used; **both contingency slots unused**.
- **Peak allocated 3133.4 MiB in all ten runs** — geometry sets training memory, nothing else.
- **EXP-032:** 202.0 MiB spare at 512×1536 for all four candidates; **WDDM spill signature
  absent** (device near ceiling, but RSS *lower* than at 512×512).
- **EXP-033:** **0 of 252** near-copy flags, holdout control at a comparable distance. `dHash ≤ 6`
  remains a **coarse indicator, not proof**.
- `.venv/Scripts/python.exe -m pytest` → **289 tests**. **No linter installed.**
- `dataset-v1.csv` byte-identical to `cd18cbb0…`; style kit `fc11d828…`, smoke kit `a8052f44…`,
  prompt kit `c40749bc…` all unchanged.
- Both human scoring artifacts hash-locked in pytest and pinned in `.gitattributes`:
  Gate 1 `cf6bf260…`, Gate 2 `835488f3…`.

### Next milestone

**M7 — Prototype 5, the integrated MVP.** Must begin **2026-08-10 to 08-12**. It inherits: SD 1.5
+ three per-style LoRAs at weight 0.7 + IP-Adapter @ 0.55, deck geometry from *generation* at
512×1536, a **binding 202 MiB memory ceiling**, and `retro-poster` shipping with its limitation
stated rather than as an equal.

## Prior state (M6 Phase B, before gate 2)

### PHASE B COMPLETE — gate 2, now closed

**Gate 1 is closed.** Kylian scored the blinded pilot sheets, fixed the scores, supplied their
sha256 **before** the blinding map was opened, and made all six decisions himself. Full record:
`docs/evidence/prototype-4/GATE-1-approval.md`. **Phase B executed exactly that approval and
decided nothing further.**

*Historical section. Its gate-2 instructions were satisfied on 2026-08-05 and are superseded
by the section above.* The handover was `docs/evidence/prototype-4/GATE-2-handover.md`, the blank
form `gate-2-scoring-form.md`, and the completed one `gate-2-scoring-form-completed.md`.

### ⚠️ Six things that applied before gate 2 closed

1. ~~Do not select a production checkpoint, a default LoRA weight, or a winning style.~~ —
   **satisfied.** Phase B selected none of them; Kylian selected all three at gate 2, and no
   automated indicator stood in for one.
2. ~~Do not finalise DR-010.~~ — **satisfied.** It stayed a draft with an empty decision section
   until his scores existed, and is now **accepted**.
3. **Do not run a contingency training run** — **still in force.** Gate 2 authorised none, and
   both slots remain unused.
4. **Do not edit any human score**, and do not let `pilot-scoring-form-completed-blind.md`
   change: a pytest asserts its sha256 `cf6bf260…`, and `.gitattributes` keeps Git from
   rewriting its line endings. If that test fails, a score was altered after unblinding.
5. **Do not describe 202.0 MiB as comfortable headroom**, and never silently reduce geometry.
6. **Do not close M6, move it to Done, push, or begin M7.**

### Gate-2 decisions — all returned 2026-08-05

Production checkpoints (300 / 600 / 300) · weight 0.7 · RQ5 per-style selected, multi-style
viable · H4 confirmed · H5 supported · PASS / PASS / PARTIAL PASS · no contingency · DR-010
finalised. Recorded in `GATE-2-approval.md`.

### Phase B measured results (4 runs, 4 passes, tier 0, no escalation)

| run | style | steps | s/step | wall | first → last loss | L2 |
|---|---|---:|---:|---:|---|---:|
| EXP-027 | minimal-geometric | 600 | 0.283 | 175.9 s | 0.0780 → 0.0025 | 4.752 |
| EXP-028 | ukiyo-e | 600 | 0.398 | 244.1 s | 0.6583 → 0.2297 | 4.080 |
| EXP-029 | retro-poster | 600 | 0.308 | 189.5 s | 0.4973 → 0.1425 | 4.972 |
| EXP-030 | **multi-style** | 1800 | 0.350 | 633.8 s | 0.6290 → 0.1960 | 8.307 |

- **Peak allocated 3133.4 MiB in all ten runs of the milestone** — geometry sets training
  memory; style count, image count and step count do not.
- **Multi-style exposure is asserted, not hoped for:** `minimal-geometric:600;
  retro-poster:600; ukiyo-e:600`. An unbalanced run raises an error rather than producing a
  plausible adapter.
- **EXP-031:** 252 generations against a cap of 432, 21 fresh processes, approved candidates
  only. **EXP-032:** 8 runs, **202.0 MiB spare** at 512×1536 for every candidate, and the WDDM
  spill signature is **absent** (device near ceiling but RSS *lower* than at 512×512).
  **EXP-033:** **0 of 252** near-copy flags, holdout control at a comparable distance.

### Three defects found in my own work — do not "re-discover" these

1. **Training is not bit-reproducible from the recorded seed (risk R14).** The LoRA
   initialisation draws from the unseeded global torch RNG. Same-step adapters differ by an L2
   of ~158 against a norm of ~112 — the √2 ratio of independent draws — while training moves
   the weights by ~5. **The data pipeline IS deterministic** and was verified so. **Not fixed
   mid-milestone on purpose:** seeding it would alter every run the gate-1 arms were compared
   against. A shipped checkpoint must therefore be preserved as an artifact, not treated as
   regenerable.
2. **24 duplicate generations in the final matrix.** Blocks A and B overlap at weight 0.7. They
   were byte-identical, but each put a self-pair into a diversity cell and pulled it toward
   zero. Fixed in the plan and the diversity pass, guarded by a test; **the matrix was not
   regenerated**, because its evidence is a valid superset of the fixed plan. Executed rows
   carry fingerprint `da7e4c36…`; the fixed plan's is `c58364681c08…`.
3. **`core.autocrlf` would have broken the scoring artifact's hash lock.** `.gitattributes` now
   pins that file, the frozen manifests and the recorded run evidence to verbatim bytes.

### Run budget

**10 of 12** training runs used (6 pilots + 3 full + 1 multi-style). **Both contingency slots
remain.** Final matrix used 252 of 432. **Hard stop 2026-08-09 EOD**; M7 must begin 08-10…08-12.

### Frozen and verified at the end of M6

- `dataset-v1.csv` **byte-identical** to `cd18cbb0…`, read-only throughout, asserted by pytest.
- Style kit **`fc11d828…` unchanged by Phase B** — the final matrix's prompts live in
  `ml/training/final_matrix.py` precisely so the kit fingerprint would not move.
- Prompt kit `c40749bc…` and smoke kit `a8052f44…` unchanged.
- `.venv/Scripts/python.exe -m pytest` → **284 tests**. **No linter installed.**
- Regenerate with: `ml.training.train_lora` (`--style`, or `--multi-style --per-style-steps`) ·
  `scripts/validate_p4_full_runs.py` · `scripts/run_final_matrix.py` ·
  `ml.training.combined_stack` · `scripts/evaluate_p4_final_indicators.py` ·
  `scripts/build_p4_gate2_package.py` · `scripts/build_p4_gate2_zip.py`.
- **Adapters and images are git-ignored** in `outputs/`; re-run training to regenerate them.

## Prior state (M6 Phase A, 2026-08-04)

### PHASE A COMPLETE — gate 1, now closed

*Historical section, kept for the record. Its gate-1 instructions were satisfied on
2026-08-05 and are superseded by the Phase B section above.* The handover was
`docs/evidence/prototype-4/GATE-1-handover.md`; the blank blinded form is
`docs/evidence/prototype-4/pilot-scoring-form.md`, and the completed one is
`pilot-scoring-form-completed-blind.md`.

### ⚠️ Five things that applied before gate 1 closed

1. ~~Do not start Phase B without Kylian's six decisions~~ — **satisfied.** All six were
   returned on 2026-08-05; nothing in Phase A selected any of them.
2. ~~Do not open the blinding map for him.~~ — **satisfied.** It was opened only after the
   scores were fixed and their sha256 verified, and no score changed afterwards.
3. **Do not let the automated indicators decide anything.** EXP-026 populates no rubric cell,
   selects no checkpoint and chooses no hyperparameter. `dHash ≤ 6` is a **coarse near-copy
   indicator, not proof of memorisation**.
4. **H4 is STILL not answered** — it carried past gate 1 unchanged and is now a gate-2
   question. The 97 % border-darkness flag on `retro-poster` is an *indicator*; whether the
   LoRA learned the frame is Kylian's failure-mode probe.
5. **No visual-quality claim was made in Phase A, and none may be added retroactively.**

### Gate 1 status (2026-08-05)

**Superseded.** Kylian first acknowledged gate 1 without scores, and Phase B stayed blocked —
acknowledgement is not approval. He then returned the fixed scores and all six decisions later
the same day, which is what unblocked Phase B. See `GATE-1-approval.md`.

A review-only ZIP was built on request at
`outputs/m6-gate-1-blinded-review-package.zip` (509 KB, sha256 `fb467e1d5b5667f3…`):
the handover, the blank scoring form, the 12 blinded sheets and the 3 base controls — **17
members, and the blinding map deliberately excluded.** It is a **derived copy in git-ignored
`outputs/`**; nothing tracked was modified, and rebuilding it changes no evidence. Regenerate
by copying those same 17 files, or re-run `scripts/build_p4_review_package.py` first if the
sheets themselves are missing.

Two leakage checks were run on the shipped text, and both must be repeated if the package is
rebuilt: the handover names arms and **never** a blind label, the form names blind labels and
**never** an arm, and all 15 JPEGs carry **zero EXIF and zero text metadata**. The only file
joining label to arm is the excluded CSV.

### Run budget

**6 of 12** training runs used. Remaining: ≤3 full, ≤1 multi-style, ≤2 contingency.
Pilot matrix used **108/108** allowed generations. Final matrix cap **432**, and only for
checkpoints Kylian approves. **Hard stop 2026-08-09 EOD.**

### Frozen and verified

- **Style kit `fc11d828…`** (`ml/training/style_kit.py`), hash-locked like `prompt_kit` and
  `smoke_kit`. Prompt kit `c40749bc…` and smoke kit `a8052f44…` **unchanged**.
- **Triggers `xgeo` / `xkyo` / `xpst`** — the plan's original `dfgeo`/`dfukiyo`/`dfposter` were
  **rejected on measured tokenizer evidence**: `dfukiyo` split into 4 pieces and lost the
  shared prefix; `dfposter` contained `poster</w>`, which sits in its own style phrase; `xuki`
  collided because ukiyo-e captions contain the literal words "uki e". The selected family is
  2 pieces each, shares a leading piece, and has **zero** corpus overlap.
- **No tokenizer vocabulary added** — the text encoder is frozen, so an added embedding would
  never be trained. A test asserts the vocab size.
- **`dataset-v1.csv` is byte-identical to `cd18cbb0…`**, asserted by pytest. It was opened
  read-only throughout.
- **Five manifests**: `style-{minimal-geometric,ukiyo-e,retro-poster}-p4.csv` plus nested
  `-n12` / `-n24` arms (**n12 ⊂ n24 ⊂ n44**, asserted). An exclusion ledger accounts for all
  148 dataset items; **no train item is excluded**.
- **Caption strategy: style-only, no trigger collision, and it is UNDER TEST** — EXP-023 is the
  verbatim counterpart, blinded.

### Measured results (6 runs, 6 passes, tier 0, no escalation)

| arm | style | captions | images | pres./item | s/step | first → last loss |
|---|---|---|---|---|---|---|
| EXP-020 | minimal-geometric | style-only | 44 | 6.818 | 0.284 | 0.0780 → 0.0044 |
| EXP-021 | ukiyo-e | style-only | 44 | 6.818 | **0.408** | 0.6583 → 0.0302 |
| EXP-022 | retro-poster | style-only | 36 | 8.333 | 0.294 | 0.4973 → 0.0351 |
| EXP-023 | minimal-geometric | **verbatim** | 44 | 6.818 | 0.294 | 0.0781 → 0.0045 |
| EXP-024n12 | minimal-geometric | style-only | **12** | **25.000** | 0.296 | 0.0648 → 0.0042 |
| EXP-024n24 | minimal-geometric | style-only | **24** | **12.500** | 0.331 | 0.0849 → 0.0052 |

- **Peak allocated 3133.4 MiB in all six** — neither style nor set size moves training memory;
  only geometry does (EXP-016/017).
- **The RQ4 equal-compute confound is measured, not assumed**: 25.000 / 12.500 / 6.818
  presentations per item. This measures **set size at equal compute, not equal epochs**, for
  `minimal-geometric` only, and **must not be generalised** to the other styles.
- `ukiyo-e` is slowest per step because its sources reach 4000 px — a **data-loading** cost.
- **EXP-025**: 108/108 generations at the cap. **EXP-026**: **0/108** near-copy flags; holdout
  control at a comparable distance to training, which is the point of the control.

### Pre-training audit (evidence for H4, gathered before any run)

| style | visual / attribution / truncated | distinct phrases | border delta | flagged |
|---|---|---|---|---|
| minimal-geometric | 44 / 0 / 0 | **6** | +17.5 | 11/44 |
| ukiyo-e | 32 / 5 / 7 | 41 | +29.7 | 2/44 |
| retro-poster | **14** / 16 / 0 (+6 venue) | 28 | **−73.5** | **35/36** |

### M6 facts a new session must know

- `.venv/Scripts/python.exe -m pytest` → **260 tests**. **No linter installed.**
- Regenerate with: `scripts/build_style_manifests.py` · `build_caption_audit.py` ·
  `ml.training.train_lora --style <s> [--manifest …] [--caption-mode …]` ·
  `scripts/run_pilot_matrix.py` · `evaluate_p4_memorisation.py` · `build_p4_review_package.py`.
- **Adapters and images are git-ignored** in `outputs/`; re-run training to regenerate them.
- The M5 runner is unchanged for M5 use — with no `--style` the spec is what it was, asserted
  by test.

## Prior state (M5, completed 2026-08-04)

**Last updated:** 2026-08-04 (M5 / Prototype 3 execution session, under Opus 5)

## M5 (Prototype 3 — LoRA smoke test): COMPLETE

**No human review gate was used, by Kylian's decision** — M5's acceptance is automated and
measurable, following the EXP-007 precedent. **No style-quality claim is made anywhere.**
Issue #6 closure, board move, and any push are **not done**: `gh` was not on PATH in this
session. Verify with `gh issue view 6` and `git status -sb` rather than trusting this line.

**Decision (DR-009): LoRA selected** for Prototypes 4–5 — rank 8 / alpha 8, UNet attention
(`to_q,to_k,to_v,to_out.0`), text encoder and VAE frozen, training memory **tier 0**.

### ⚠️ Four things the next session must not soften

1. **R12 is re-scoped, NOT closed.** The combined SD 1.5 + LoRA + IP-Adapter stack **fits at
   512×1536 — by 202.0 MiB of 8187.5, which is 2.5 % of the device.** That is *less* margin
   than IP-Adapter alone had (222 MiB). **Never call it comfortable headroom.** Prototype 5
   must treat this as the **memory ceiling of the production path**: a second adapter, a
   higher rank, a bigger reference batch, or ControlNet all have 202 MiB to fit into.
2. **DR-009 makes no superiority claim.** From-scratch, full fine-tuning, DreamBooth and
   Textual Inversion were **screened, never measured**. The defensible statement is that
   LoRA is the mandated method *demonstrated feasible* on this hardware. Do not upgrade
   this to "best" in the report.
3. **No long native 512×1536 training run has happened.** EXP-017 was a **feasibility probe
   only** (1 and 10 steps). Expanding it is a **separate M6 decision that needs Kylian**.
4. **Gradient accumulation is not a memory tier**, and a guard enforces it. At micro-batch 1
   it changes effective batch size, not micro-step peak memory. Kylian caught this in plan
   review and the measurements confirmed him.

### Measured results (13 runs across 8 experiments, tier 0 throughout, zero escalations)

| run | geometry | peak alloc | peak device | spare | s/step |
|---|---|---|---|---|---|
| EXP-016a (1 step) | 512×512 | 3114.09 | 4267.5 | 3920.0 | 1.9344 |
| EXP-016b (10 steps) | 512×512 | 3133.40 | 4285.5 | 3902.0 | 0.4340 |
| EXP-016 (300 steps) | 512×512 | 3133.40 | 4285.5 | 3902.0 | 0.2854 |
| EXP-017a (1 step) | 512×1536 | 5160.96 | 6429.5 | 1758.0 | 2.5533 |
| EXP-017b (10 steps) | 512×1536 | 5182.58 | 6449.5 | 1738.0 | 1.1223 |
| **EXP-019a** (LoRA+IP-Adapter) | 512×512 | 3927.11 | 5697.5 | 2490.0 | — |
| **EXP-019b** (LoRA+IP-Adapter) | **512×1536** | **5143.73** | **7985.5** | **202.0** | — |

- **Activations scale with geometry; optimizer state does not.** Post-load allocation is
  identical at both geometries (2066.56 MiB) and the optimizer-step peak barely moves
  (2108.93 → 2118.76) while forward/backward rises 3114 → 5183. **So gradient checkpointing
  (tier 1) is the correct first escalation**, not a lower-memory optimizer.
- **A rank-8 LoRA costs +3.04 MiB allocated at BOTH geometries** — measured independently in
  EXP-018 and EXP-019. It does not scale with output size.
- **300 training steps cost 91 s.** Prototype 4's comparison grid is affordable many times over.
- **EXP-018:** reload proven from the **live UNet** (0 → 128 LoRA modules). Weight 0.0 gave
  **4/4 byte-identical** to baseline — a **diagnostic, not a pass condition**. Weight 1.0 gave
  **4/4 beyond a pre-declared noise floor** (mean abs pixel diff 51.89–66.33, dHash 20–28,
  CLIP cosine 0.4796–0.7247). A differing PNG hash alone was never treated as sufficient.
- **Cross-milestone continuity holds for a third milestone:** the EXP-018 baseline peak of
  **2675.38 MiB is byte-identical** to Prototype 1's EXP-002 and Prototype 2's text-only baseline.

### M5 facts a new session must know

- `.venv/Scripts/python.exe -m pytest` → **210 tests**. Frozen prompt kit `c40749bc…` unchanged;
  **new smoke kit fingerprint `a8052f44…`** hash-locked the same way. **No linter is installed.**
- **`peft==0.20.0`** pinned in `ml/requirements-training.txt`, installed `--no-deps` after a
  parsed `--dry-run --report` proved it moved none of torch / diffusers / transformers /
  accelerate / safetensors. **Never install `bitsandbytes` or `xformers` without Kylian's
  approval** — both confirmed absent, and no 8-bit-optimizer support may be claimed.
- **Frozen smoke subset:** `data/manifests/smoke-test-p3.csv`, 12 `minimal-geometric` **train**
  items, deterministic rule (sort by id, first 12), covering all 6 palettes and 6 shape counts.
  Holdout exclusion is proven **against dataset-v1**, not against the manifest's own column.
- **Caption strategy: dataset-v1 captions verbatim, NO trigger token** — deliberate, so the
  smoke test carried one variable. **Trigger-token design is an open M6 decision.**
- **The training tier ladder is NOT the inference ladder** (`ml/training/lora_schema.py`);
  a test asserts they stay distinct so "tier 2" cannot mean two things.
- **Import boundaries are AST-parsed, not text-scanned.** The schema imports no torch; neither
  training runner may import the CLIP evaluator. Phase 1 (train/generate) and Phase 2
  (similarity) stay separate processes.
- Regenerate with: `scripts/build_smoke_test_manifest.py` · `scripts/run_lora_training.py`
  (`--plan`, `--stage`, `--dry-run`) · `scripts/build_p3_training_summary.py` ·
  `scripts/evaluate_lora_effect.py` · `ml.training.verify_lora` · `ml.training.combined_stack`.
- **`outputs/` is git-ignored** — ~31 MB of adapters and images live there. Only manifests,
  summaries and contact sheets are committed. **Model weights are never committed.**
- The **EXP-016 smoke adapter** used by EXP-018/019 is
  `outputs/lora/EXP-016__smoke__512x512__r8a8__lr0p0001__bs1x1__st300__seed42__tier0/`,
  sha256 `e76f822bd3b6314a…`. It is git-ignored — **re-run EXP-016 to regenerate it**.
- One honest failure is preserved: the first **EXP-019a** row has `status: failed`, a defect in
  that runner (`preprocess_for_adapter` returns `(image, note)`), **not** a finding about the
  stack. Do not delete it.

## Prior state (M4, completed 2026-08-01)

### M4 (Prototype 2 — text + reference-image conditioning): COMPLETE

**Human review passed 2026-08-01; conditioning method selected in DR-008.** Issue #5 closure, board
move to Done, and the push to `origin/main` follow this commit — verify their real state with
`gh issue view 5` and `git status -sb` rather than trusting this line.

**Decision (DR-008):** **standard IP-Adapter selected** as the primary reference-conditioning
method for Prototypes 3–5 (`h94/IP-Adapter`, `ip-adapter_sd15.safetensors` @ `018e402774`).
**Default scale 0.55**, user-adjustable **0.40–0.60**; higher values only with an explicit warning
that prompt authority falls and pseudo-text / source-like composition increase. **img2img is a
documented zero-extra-VRAM fallback, not the default path.** IP-Adapter-Plus not selected.
ControlNet stays criteria-only, deferred to Prototype 5 for layout control.

### ⚠️ Two things the next session must not soften

1. **R12 (open, high/high) — the combined stack may not fit.** IP-Adapter alone at 512×1536 peaks
   at **7965.5 MiB of 8187.5 MiB physical, about 222 MiB spare.** **Never describe this as
   comfortable headroom.** A **combined SD 1.5 + selected LoRA + IP-Adapter smoke test at 512×1536
   is a mandatory acceptance item for M5** — it is in the M5 planning row as scope, dependency and
   required evidence. If it fails, record the failure as its own result row and test the approved
   memory tiers in separate runs. **Never silently reduce geometry to make it pass.**
2. **R13 (occurred, mitigated) — img2img reproduces the reference at the deck format.** All six
   copy-risk flags in M4 (dHash ≤ 6) are img2img at 512×1536, three at **dHash 0–1**. Median dHash
   for img2img at medium is 27 @512×512 but **5 @512×1536**. Keep the dHash ≤ 6 flag and the
   copy-risk sheet in every future evaluation. Prototype 5 must not expose an img2img mode at the
   deck format without this warning.

### Measured results (299 generations, zero failures, tier 0 throughout)

| geometry | text-only | img2img | IP-Adapter | Plus |
|---|---|---|---|---|
| 512×512 | 2675.38 MiB | **2675.38 (+0.00)** | 3924.07 (+1248.69) | 3978.87 |
| 512×1536 | 3892.01 MiB | **3892.01 (+0.00)** | 5140.69 (+1248.68) | not measured |

- **img2img costs exactly zero extra VRAM**; IP-Adapter's ~1249 MiB overhead is **identical at both
  geometries**, because its scale acts on attention rather than on output size.
- **Latency trap:** img2img wall-clock *falls* as influence rises (3.021 s → 1.208 s) because
  diffusers runs `int(steps × strength)` steps. Per-effective-step cost is flat at 0.112–0.134.
  **Fewer steps, not faster ones** — never quote img2img as intrinsically faster.
- **Process isolation accepted in full:** 6/6 spot-check pairs at +0.000 % against a 2 % tolerance
  pre-declared in code.
- **Lower bound met exactly:** 12/12 IP-Adapter runs at `scale=0.0` byte-identical to the text-only
  baseline; 12/12 M4 baselines byte-identical to Prototype 1's EXP-002, so **M3 and M4 figures are
  directly comparable**.
- **Monotone in 6/6 conditions for both methods.** IP-Adapter-Plus is *not applicable* (one level
  by design), never "failed".

### Human scores (Kylian, 2026-08-01) — read before re-scoring anything

Recorded at **aggregate (method × level × resolution)**, which is exactly the form's row granularity,
so unlike M3 they are entered directly rather than marked "not individually scored".
`docs/evidence/EXP-015-scoring/human-scores.csv` is authoritative; the form and probe are generated
from it.

**29 cells are NOT SCORED. A blank is never a zero and must never be back-filled.** They are
excluded from every mean and the surviving `n` is printed beside each figure.

- `reference_influence` / `copy_or_overfitting_risk` blank for **text-only** — it uses no reference.
- `diversity_across_seeds` has **n=1 per method** — not load-bearing, do not lean on it.
- **`text-only` at 512×1536 is entirely unscored. Do not substitute an M3 value** — the M3 review
  used different sheets and answered a different question.

Means at 512×512 (blanks excluded): originality **img2img 3.12 (n=8) vs ip-adapter 4.11 (n=9)**;
copy risk **3.12 vs 4.33**. At the deck format img2img scored originality 1 / copy risk 1;
IP-Adapter 4 / 4.

### M4 facts a new session must know

- `.venv/Scripts/python.exe -m pytest` → **123 tests**; frozen-kit fingerprint `c40749bc…` unchanged.
- **No linter is installed** (`ruff` absent). pytest is the validation gate — never claim a lint step ran.
- Adapter cache: `h94/IP-Adapter` **2453.8 MiB**, outside the repo. Both adapter and image encoder are
  pinned to `018e402774…`; **diffusers 0.39.0 does not forward `revision` to the image encoder**, so
  the runner registers a pinned encoder itself before `load_ip_adapter`. Do not remove that workaround.
- **Measurement instrumentation must never enter the workload it measures.** Phase 1 (generation) and
  Phase 2 (similarity) are separate processes; pytests enforce the import boundary in both directions.
- Regenerate anything with `scripts/`: `build_reference_kit.py` · `run_reference_conditioning.py`
  (`--dry-run`, `--only`, `--start-at`) · `evaluate_similarity.py` · `build_p2_analysis.py` ·
  `build_p2_contact_sheets.py` · `build_p2_scoring_form.py` · `summarise_p2_human_scores.py`.
- `deliverables/` is **git-ignored** — a derived upload package duplicating tracked evidence.

## Prior state (M3, completed 2026-07-30)

Phase 0, public planning (issues #1–#12), **M1 (Prototype 0)**, and **M2 (dataset)** complete and pushed.

**M3 (Prototype 1 — base-model benchmark): COMPLETE.** Human review passed 2026-07-30; issue #4 closed as completed; board shows M3 Done.

**Decision (DR-007):** **SD 1.5 selected** as the base model for Prototypes 2–5 (pinned `451f4fe1`). SDXL base 1.0 is the **visual-quality winner at native 1024×1024** but is retained as a benchmark, not the production model. **Deck format: direct 1:3 at 512×1536**; square-crop rejected. Third candidate SD 2.1 base **blocked** (HTTP 401), so the comparison rests on **two** measured candidates — a limitation that must be stated in the report.

## Uncommitted changes

None expected at handoff — verify with `git status`.

## Latest commits (M6 Phase A sequence, 2026-08-04/05)

> **SUPERSEDED — this paragraph was true when written and is not true now.** The whole M6
> sequence was pushed; `origin/main` reached `6d1b24b` on 2026-08-05. The current unpushed work
> is M7's, listed in the M7 section at the top of this file.

*Historical:* "`main` is 8 commits ahead of `origin/main`. NOTHING IS PUSHED, and no push may
happen before Kylian approves it." M5 ended at `9ebb7a2`.

```
0f1389e docs(process): record prototype 4 phase a and stop at the human review gate
ed23abf feat(evaluation): add the blinded prototype 4 gate-1 review package
2b98f65 docs(experiments): record prototype 4 memorisation indicators, offline on cpu
5ffe057 feat(evaluation): add the capped prototype 4 pilot review matrix
66cd0a4 docs(experiments): record prototype 4 pilots, caption a/b and dataset-size arms
0611319 feat(training): extend the training runner for per-style runs and loss history
3226a33 docs(dataset): audit prototype 4 captions and source images before training
b42e693 feat(training): freeze the prototype 4 style kit and per-style manifests
9ebb7a2 docs(process): close prototype 3 across planning, risks, testing, and traceability  <- last pushed
```

Earlier M3/M4/M5 commit sequences are in the process log rather than repeated here.

## Human scores (Kylian, 2026-07-30) — read before re-scoring anything

Recorded at **aggregate model/track level**, not per unit. `docs/evidence/EXP-006-scoring/human-scores.md` is authoritative; per-unit cells in `scoring-form.md` read "not individually scored" **on purpose** — do not back-fill them with the aggregates.

- Track A (both @512): SD 1.5 and SDXL scored **identically** 3/3/4/3/3/4/3.
- Track B native: SD 1.5 3/3/4/3/3/4/3 · SDXL **4/5/5/4/4/4/3**.
- `reference_influence` = **N/A** until Prototype 2. `diversity_across_seeds` = **not scored**, because the review sheets showed only the fixed seed-42 comparison. **Do not invent a value** — a multi-seed sheet is needed first.

## Measured results (all at tier 0; no escalation needed)

All at memory tier 0; no tier escalation was needed anywhere.

| Experiment | Result |
|---|---|
| EXP-001 | CUDA PASS. torch 2.13.0+cu126, bundled runtime 12.6, driver 610.88, RTX 4060 Laptop sm_89, 8187.5 MiB |
| EXP-002 SD 1.5 | 30/30 ok. 512×512 median **4.07 s**, alloc 2675 MiB. 512×768 median 6.81 s, alloc 2979 MiB |
| EXP-003 SD 2.1 base | **BLOCKED** — HTTP 401, repository gated. Two candidates by Kylian's decision |
| EXP-004 SDXL base | 30/30 ok. 512×512 median 16.51 s, alloc 7859 MiB. 1024×1024 median **118.73 s**, alloc **10738 MiB** |
| EXP-005 aspect ratio | 24/24 ok. 512×1536 median 15.24 s in 3892 MiB; square-crop leaves only **170×512 usable** |

**Do not report SDXL as "works on 8 GB".** Its 1024×1024 peak allocated (10738 MiB) and reserved (14510 MiB) exceed the 8187.5 MiB physical VRAM; WDDM spilled silently into host RAM instead of raising a CUDA OOM, so nothing failed and no tier escalated. It degraded quietly. ~29× SD 1.5's cost per 512 px image.

## Facts a new session must know

- Repo root: `C:\Expert Lab\Selftrained-and-deployed-AI-image-generator`; **8 GB VRAM** is the hard constraint.
- **Python:** `.venv` at repo root is **Python 3.11** (`.venv/Scripts/python.exe`). Never use system Python 3.14. Run tests with `.venv/Scripts/python.exe -m pytest` (66 tests, `pytest.ini`, testpaths=ml). Set `PYTHONIOENCODING=utf-8` for scripts that print non-ASCII.
- **pip 22.3 shipped in the venv cannot resolve torch** (rejects underscore-normalised wheel metadata). It was upgraded to 26.2; do not downgrade.
- **PyTorch install is NOT from PyPI:** `--index-url https://download.pytorch.org/whl/cu126`, `torch==2.13.0+cu126 torchvision==0.28.0+cu126`. See `ml/requirements-inference.txt` for the full rationale. `nvidia-smi`'s CUDA version is the **driver's max supported API**, not a toolkit to match. No xformers (torch SDPA is the Diffusers default). No nightlies.
- **Frozen evaluation kit** in `ml/evaluation/prompt_kit.py`, fingerprint `c40749bc100deea5cc5854e40ba34928dcf3fdda31ff3c41840dafdfba1f5228`, hash-locked by pytest. **Never edit it to fix a benchmark** — record deviations per run instead. Changing it invalidates comparability with every earlier experiment.
- **One configuration per OS process** whenever VRAM or timing is measured. Adopted after a real contamination incident: the caching allocator retains its pool across `reset_peak_memory_stats()`, which corrupted EXP-005's first run. See `docs/evidence/EXP-005/measurement-methodology-correction.md`.
- **Model revisions are pinned to commit SHAs:** SD 1.5 `451f4fe16113bff5a5d2269ed5ad43b0592e9a14`, SDXL `462165984030d82259a11f4367a4eed129e94a7b`. HF cache lives outside the repo at `C:\Users\kylia\.cache\huggingface` (~14 GB for SDXL alone).
- **`outputs/` is git-ignored** — 84 full-resolution PNGs live there. Only manifests, summaries, and contact sheets (≤300 KB) are committed.
- **Style identifiers** are `retro-poster`, `minimal-geometric`, `ukiyo-e`. `retro-poster` was renamed from `retro-comic` on 2026-07-30 because the material is WPA silkscreen posters, not comics. Never reintroduce `retro-comic`; pytest regression guards enforce this.
- **Dataset:** 148 items, splits 124/17/7, manifest `data/manifests/dataset-v1.csv`, raw images git-ignored.
- `apps/web`: React 19 + Vite 6.4.3 + R3F viewer (M1); `npm run dev/test/build`.

## Blockers (historical — M6 Phase A era; superseded by the M7 section at the top)

- ~~**M6 Phase B is blocked on Kylian's gate-1 review.**~~ **Satisfied 2026-08-05.** This is the intended state, not a
  failure: the milestone deliberately stops here. Nothing may be worked around, and no
  automated indicator may stand in for a decision he has not made.
- **`gh` is not on PATH**, so issue #6 and #7 state could not be verified or changed from
  here. Both remain Kylian's, along with any push.
- **Three M5 decisions are still open** and Phase B does not need them resolved to start:
  whether a long native 512×1536 training run happens (only feasibility was probed);
  whether Textual Inversion / DreamBooth get measured comparisons or stay screened-only with
  the limitation stated in the report; and the M2 framed / matted `retro-poster` mitigation
  (crop pass vs negative prompting), which now has EXP-022 and the caption audit behind it.
  Trigger-token design — the third M5 open decision — **is now closed** by the frozen
  `xgeo` / `xkyo` / `xpst` family.

## Next action (historical — M6 Phase A era)

> **SUPERSEDED.** The current next action is Kylian's **M7 review gate**; see the top of this
> file and `docs/evidence/prototype-5/GATE-handover.md`. The M6 text below was satisfied on
> 2026-08-05 and is kept for the record only.

**Wait.** Do not start Phase B, and do not do preparatory Phase B work that presumes an
answer. When Kylian returns the scored form he must also return the **six decisions** listed
in `docs/evidence/prototype-4/GATE-1-handover.md` §6:

1. **Checkpoint per style** — 150 or 300, for each of the three styles.
2. **Full-run step count per style** — within the pre-declared band **600–1500**.
3. **Caption verdict** — style-only / verbatim / trade-off / tie-inconclusive.
4. **Dataset-size verdict** — O1 monotone / O2 plateau / O3 no effect / O4 trade-off /
   O5 inconclusive.
5. **Contingency** — authorised or not, and if so which **single** variable it may change.
6. **Multi-style** — whether the balanced run proceeds.

Then Phase B runs, in this order and no other: approved full per-style runs (EXP-027/028/029)
→ any authorised contingency → the multi-style run if approved (EXP-030) → the final
validation matrix on **approved checkpoints only**, capped at **432** (EXP-031) →
combined-stack checks against the **202 MiB** margin (EXP-032) → **DR-010 as a draft with no
conclusion** → **gate 2**.

**If Kylian returns scores but not all six decisions, ask for the missing ones. Do not infer
them from the rubric, and do not let a high score select a checkpoint.**

**2026-08-09 EOD is the hard stop whatever state M6 is in**, and M7 integration must begin
2026-08-10 to 08-12. If the gate is still open close to that date, the scope-reduction order
applies: keep `minimal-geometric`, then `ukiyo-e`, then reduce or drop `retro-poster` — and a
dropped style is **stated as dropped, with the reason and date**, never quietly removed.
