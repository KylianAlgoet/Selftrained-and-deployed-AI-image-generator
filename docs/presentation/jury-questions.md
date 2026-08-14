# Jury questions — the material that came off the stage deck

**Purpose.** The defence slot is **20:00 including the live demo**, which allows roughly 15 minutes
of narration. The deck was cut from 26 slides to 15 to fit it (DR-017). **Nothing was deleted from
the project** — the content below left the *visible slides* and lives here, in the speaker notes, and
in the research report.

Each entry is written to be answered in **30–60 seconds** from the stage, with the evidence path
attached so the claim can be checked afterwards. Every figure here is already evidenced elsewhere;
this file introduces no new claims.

**Read the honesty bounds first.** If a question pushes toward a stronger claim than the evidence
supports, the answer is the bound, not the flattering version. The four that matter most:
`retro-poster` is a **partial pass**, the image-count question is **inconclusive**, LoRA is
**feasible, not proven best**, and **training is not reproducible from seed** while inference is.

---

## 1. Slides that were cut, and what to say if asked

### "You mentioned reading memory against the ceiling — say more."

*Was slide 10 of 26. Now folded into the base-model slide's note.*

**A successful run is not a run that fitted.** Those are different claims and modern systems blur
them: the driver spills to host RAM, the caching allocator holds its pool, the OS swaps, and the
process exits zero throughout. SDXL completed all thirty benchmark runs and reported success while
allocating well over the card's capacity.

So from EXP-005 onward every memory figure is read against the **8187.5 MiB ceiling**, never
against whether anything crashed. It also cost me one measurement error: the caching allocator holds
its pool across a reset, which contaminated an experiment until I switched to **one configuration
per process**. Documented rather than quietly fixed, because the wrong method produced perfectly
plausible numbers.

**Evidence:** EXP-005 · `docs/technical/environment-audit.md` · report §19.3

### "What exactly ships, and how do you know it has not been swapped?"

*Was slide 14 of 26 (the adapter table). Now one line on the LoRA slide.*

| style | experiment | ships at | verdict |
|---|---|---|---|
| `minimal-geometric` | EXP-027 | step 300 | pass |
| `ukiyo-e` | EXP-028 | step 600 | pass |
| `retro-poster` | EXP-029 | step 300 | **partial pass** |

Each adapter is **6 414 480 bytes**, 256 tensors, 256 LoRA keys and **zero base-model keys**. The
SHA-256 of each is verified **when the style is activated, on every request** — not once at startup.
Because the weights cannot be regenerated (see determinism), the files are the authority, and a
per-request integrity check is what would catch a swap or a corruption.

**Evidence:** `docs/deployment/weights-manifest.md`, guarded by a pytest so the manifest cannot
drift from the code · DR-010

### "Why is the artwork stretched on the deck?"

*Was slide 20 of 26.*

Decals are **1:3**. The deck surface is **1:3.9**. Something has to give, so I built both options
rather than picking one: stretch to fill, which distorts the artwork about 30 % vertically, or
preserve the ratio, which leaves about 23 % of the board bare.

I chose to fill, because a graphic covering the deck reads as a finished product and one with a bare
strip reads as a bug. **The part I would defend is that the interface says so** — it tells the user
the artwork is stretched, rather than hoping nobody measures it. A trade-off the user is told about
is a design decision; the same one hidden is a defect waiting to be found. The rejected mode is
still selectable behind `?review=1`, because it is the evidence behind DR-012.

**Evidence:** DR-012, with the student's rationale quoted verbatim ·
`docs/evidence/prototype-5/screenshots/fit-*.jpg`

### "Walk me through the learning outcomes."

*Was slide 26 of 26 as a mapping table. The deck now closes on what I would change instead.*

| | |
|---|---|
| **D1 / D5 / D6** | 40 experiments, six prototypes, and conclusions bounded by what was measured — §19.5 refuses six of them explicitly |
| **D2 / D3** | 16 decision records, a planning log recording what slipped and why rather than being rewritten to match the original plan, public issues and board |
| **D4** | alternatives compared and rejected on criteria: base model, conditioning, fine-tuning method, deployment |
| **D7** | the research report, this deck, and a system that states its own limitations to its user |

**Evidence:** `docs/learning-outcome-traceability.md`, maintained as evidence was produced rather
than assembled at the end

### "Why build the 3D viewer first?"

*Was part of slide 6 of 26; the ladder diagram survives on the method slide.*

It looks like the wrong order and it was not. Building Prototype 0 before any artwork existed made
the deck's **aspect ratio and UV layout hard inputs** to the image problem instead of assumptions,
and it caught an **orientation fault** that conveniently square test images would have hidden until
the end. The general lesson — the awkward step early is cheaper than the discovery late — happened
three times in this project.

---

## 2. Questions about the method

### "Your evaluation has one rater. Is that not fatal?"

It is the limitation I would raise first, and it is on the limits slide rather than hidden here.
**One human approver, AI-assisted visual analysis, and no second independent human rater**, so **no
inter-rater agreement can be reported**. ChatGPT proposed visual analysis and scores at the gates; I
reviewed, approved and kept final authority over every recorded score and every production
selection.

What *does* protect the result: the rubric was written **before the images existed**, the first gate
was **blinded** — I scored the sheets and fixed their SHA-256 before the blinding map was opened —
and the scoring artifacts are **hash-locked in pytest**, so a score cannot be altered after
unblinding without failing the suite.

An earlier draft of the report overstated the human/AI separation. I caught it at a gate and
corrected it in nine places rather than rereading the evidence to fit the claim.

**Evidence:** `docs/evidence/prototype-4/GATE-1-approval.md`, `GATE-2-approval.md` · report §18.4

### "Is 148 images not far too few?"

Probably, and I cannot tell you the number that would be enough — that is exactly the inconclusive
result. I trained the same style on 12, 24 and 44 images with everything else fixed and got a
**non-monotonic** ordering, with **one run per condition**, so I cannot separate a real effect from
variance. Repeating each condition enough times did not fit the GPU budget.

The honest reading: 44 images was **sufficient to produce a checkpoint that passed a human gate**
for two styles. That is not the same as a minimum, and no minimum is claimed anywhere.

**Evidence:** EXP-024n12, EXP-024n24, EXP-024 · report §13

### "Did the model memorise its training data?"

**Bounded, not settled** — and the distinction is deliberate. Nearest-neighbour perceptual-hash
checks against a **7-item holdout that never entered training** flagged **0 of 252** candidates in
the final matrix, with the holdout control sitting at a comparable distance to training data, which
is the point of the control.

`dHash ≤ 6` is a **coarse near-copy indicator, not proof of memorisation**. Those checks bound the
risk; they do not disprove copying, and the report says so rather than rounding up.

The related finding is on the conditioning slide: **every near-copy flag in Prototype 2 came from
img2img**, none from IP-Adapter, and that is why the free method was rejected.

**Evidence:** EXP-026, EXP-033, EXP-035

### "What else failed that is not on a slide?"

- **SD 2.1 was never measurable** — authentication-gated. The base-model decision rests on **two**
  candidates, not three. A gap in the evidence, not a verdict on SD 2.1.
- **Two institutional sources could not be retrieved** — HTTP 429 and 403 across five official paths
  on two occasions. The wording drafted from them was **removed** and the failure recorded. That is
  the fourth time third-party hosting obstructed this project.
- **24 duplicate generations** were found in a final matrix; they were byte-identical and each put a
  self-pair into a diversity cell. Fixed in the plan and guarded by a test; the matrix was **not**
  regenerated, because its evidence is a valid superset of the fixed plan.
- **A CI runner stall** produced a 22× swing in scenario duration on identical code. Budgets were
  raised on measured evidence, and the report states that a green run under raised budgets is weaker
  evidence than a first-attempt green.

**Evidence:** report §12 (failed and blocked experiments) · `docs/evidence/M9/reference-retrieval.md`
· `docs/evidence/M8/ci/runner-stall-trace.md`

### "Prompt adherence — what happens if I ask for something complicated?"

A known, accepted limitation. **Strong style conditioning can dominate a detailed prompt.** A prompt
for *"a futuristic city skyline with a skateboarder jumping over neon buildings"* produced a clearly
`minimal-geometric` and usable deck graphic **in which neither the skyline nor the skateboarder was
clearly represented.**

It is consistent with the measured drop in prompt adherence at step 600, it is **not** a frontend
fault, and nothing was retrained or rewritten to hide it. If this happens live, say so and use it —
it is the limitation, demonstrating itself.

**Evidence:** report §17 · `docs/evidence/prototype-5/`

---

## 3. Questions about the system

### "How does the progress bar work, and why no percentage while loading?"

**Only denoising has a real denominator.** Step 14 of 30 is genuinely 14 of 30, read from the
pipeline. Loading, decoding and saving publish a **stage name and a null estimate**, and a test
enumerates every non-denoising stage to prove no number is invented for them. 100 % waits for the
PNG to decode in the browser.

I could have drawn a bar creeping to 90 % during loading. It would look better and it would be a lie
about where the time went. `Finalising the decal…` is genuinely about a second, and it is **not**
padded to make the label linger.

**Evidence:** DR-013

### "An upload endpoint attached to a GPU — how is it secured?"

Extension and MIME allowlist, **real decode validation** (the image is actually opened; failure
rejects), dimension and byte limits, **random internal filenames** so a user-supplied name never
reaches the filesystem, path-traversal prevention, temporary-file cleanup, restricted CORS, safe
error messages that leak no local paths, and a timeout on generation.

Uploads are treated as untrusted throughout, and the rules are **not configurable** — a pytest
derives the permitted settings from `config.py` by AST, after M8 found `.env.example` documenting
five variables nothing read, two of which implied upload security was tunable.

**Evidence:** `docs/evidence/M8/security/upload-security-matrix.md`

### "Why only one worker? That is not a real service."

It is a **correctness requirement**, not a deployment convenience, and it is asserted in code at
startup. The production stack leaves about **200 MiB spare** on an 8 GB card — a second resident
pipeline does not fit. So a concurrent request gets a **clean 409** rather than an out-of-memory
crash that takes the first request down with it.

You are right that it does not scale, and the report says so: scaling this is **not a configuration
change**. It needs a second GPU or a different serving architecture, and neither was in scope.

Note the process detail that caught me out: `uvicorn --workers 1` starts **two** processes, a
supervisor and a worker, so `/api/health` reports the worker's pid and stopping only the recorded
pid strands the worker on port 8000.

**Evidence:** DR-011 · EXP-034 · `docs/deployment/runbook.md`

### "Could this be hosted online?"

Not as it stands, and the reason is scope rather than impossibility. **Public cloud deployment was
deliberately not selected for this bachelor version** (DR-014, Option D of four compared on nine
criteria): it costs money for the length of the project, adds a network dependency on the one day
everything must work, and — the deciding part — answers nothing. The research question is what fits
in 8 GB of *consumer* hardware; a rented data-centre card replaces that question rather than
answering it.

The **200 MiB margin bounds a second resident pipeline on this validated GPU**. It does not make
hosting impossible in some future architecture, and I would not claim that it does.

**Evidence:** DR-014

### "How do I know someone else can run this?"

The **clean-clone test**: clone into an empty directory, install from scratch, reach a working
system — about ten minutes, following `docs/deployment/runbook.md`. It reproduced an earlier
generation **byte for byte** in a fresh environment three days later.

That is a stronger reproducibility claim than a public URL, which only proves the software runs
where I put it. The clean clone also found the defect that justifies the whole exercise: a dataset
integrity hash that had **only ever passed on the machine that wrote it**, because it hashed a CRLF
working copy while Git stores LF.

**Evidence:** `docs/evidence/M8/clean-clone/`

### "You say training is not reproducible. Is that not a serious flaw?"

Yes, and it is mine. The LoRA initialisation draws from the **unseeded global torch RNG**, so the
seed I recorded for every run never governed the part that mattered. Same-step adapters from
identical configurations differ by an **L2 of about 158** against a weight norm of about 112 — the
√2 ratio of independent draws — while training itself moves the weights by about 5.

Three things about it I would defend:

1. **The data pipeline *is* deterministic**, and that was verified separately.
2. **It was not fixed mid-milestone on purpose.** Seeding it would have altered every run the gate-1
   arms were compared against, so the fix is **forward-only** and the M6 evidence deliberately
   predates it.
3. The consequence is stated in the deployment docs: three required files **cannot be regenerated**,
   so they are preserved as artifacts and verified by hash.

I found it only because I tried to reproduce my own result instead of assuming I could.

**Evidence:** risk R14 · report §14

---

## 4. If the demo fails

Say the line on the slide, then go to **`Upload your own decal`** with a pre-generated PNG. Do not
reload, do not retry, do not open a terminal, and do not run a second generation. The fallback
ladder has four rungs and each is under 30 seconds.

**Do not generate with `retro-poster`** — it is the partial pass. Demonstrate it in words and
generate with a full pass.

**Evidence:** `docs/presentation/demo-backup-plan.md`, `demo-backup-manifest.md`, `demo-script.md`
