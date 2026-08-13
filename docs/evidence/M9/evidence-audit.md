# M9 evidence audit

**Milestone:** M9 — final research report and reproducible PDF delivery
**Date:** 2026-08-10 · **Baseline commit:** `a2d70c1` (`main` == `origin/main`, working tree clean)
**GitHub issue:** #10 — *M9 - Research report and PDF*

This is the audit performed **before** any report chapter was written. It records what evidence
exists, which record is authoritative where two disagree, and which gaps had to be closed before
the report could cite anything. It is written once and not rewritten; later corrections are
appended with their dates.

## Issue #10 acceptance criteria

Verified by Kylian from the browser; `gh` is not on PATH in the authoring environment, so no
session command could read the issue.

| # | criterion | where M9 satisfies it |
|---:|---|---|
| 1 | Every important conclusion links to real evidence, experiments, decisions, or commits | inline evidence paths per chapter; appendices A–D |
| 2 | Reproducible PDF build process documented | DR-015, `scripts/build_report.py`, appendix F |
| 3 | Spelling, links, references, and output validated | `scripts/validate_report.py` |
| 4 | Report PDF stored in `deliverables/` | `deliverables/DeckForge-AI-research-report.pdf` |

The planning row (`docs/02-planning.md`, M9) and Prompt 5 of
`docs/prompts/DeckForge_AI_Final_Claude_Code_Prompts.md` are consistent with these and supply the
mandated section list.

**An earlier draft of the M9 plan inferred the issue number arithmetically** from
`docs/02-planning.md` ("issues #1–#12" mapped to M0–M11, M8 being #9). That inference happened to
be right, but it was not evidence, and it is recorded here as superseded rather than deleted.

## Mandated report structure: 26 sections, not 24

The M9 briefing assumed 24 mandatory sections. Enumerating Prompt 5 lines 394–419 gives **26**:

executive summary · context and assignment · learning outcomes · problem statement · primary and
secondary research questions · methodology · original planning and planning changes · architecture
research · model and fine-tuning comparison · dataset methodology and licences · all prototypes ·
failed experiments · experiment results · integrated MVP · testing · deployment · ethics, copyright,
privacy and bias · limitations · conclusions · reflection · lessons learned · what should be done
differently · future work · references · appendices · D1–D7 traceability.

All 26 are mandatory. None is merged away.

## Two disagreements between records

Both were found by comparing files rather than by trusting one. Neither was resolved silently.

### 1. Generation total — 25 or 27?

| record | says | |
|---|---|---|
| `README.md` (before this milestone), older prototype docs | implies **25** | the research cap |
| `docs/02-planning.md` M8 change-log entry | **27** | with the breakdown |
| `docs/evidence/M8/README.md` | **27** | "Never reported as 25" |
| `docs/process/session-handoff.md` | **27** | with an explicit instruction not to report 25 |
| `experiments/registry.csv` | **contains neither figure** | it registers experiments, not generations |

**Authoritative: 27.** = 25 research generations (the cap, closed exactly) + 1 M7 human-review run
+ 1 M8 deployment-validation run. The last two carry **no `EXP-###`** and are deliberately absent
from the registry, because adding them would contaminate a frozen research matrix.

**Why the registry does not settle it:** the registry is a record of experiments, and two of the
27 generations were deliberately not experiments. The count therefore lives in the milestone
records, and those agree with each other. The report states **27 with the breakdown**, never a bare
number.

### 2. GPU margin — 222, 218, 202.0 or 200.0 MiB?

Four figures exist, all real, all measured under different conditions. They are a measurement
series, not a contradiction.

| MiB spare | source | condition |
|---:|---|---|
| 222 | EXP-013 | IP-Adapter alone at 512×1536, no LoRA |
| 202.0 | EXP-019b, EXP-032 | combined stack, **one-shot process** |
| **200.0** | **EXP-034** | **combined stack under real serving, 12 requests, adapter swaps** |
| 218.0 | M8 clean-clone run | combined stack, **prompt-only** (no reference image) |

**Authoritative for production: 200.0 MiB**, established by the risk-register review of
2026-08-06 and carried by DR-011, `docs/process/risk-register.md` R12 and the feature-freeze record.

**The 218.0 figure does not supersede it.** It is the prompt-only case; the reference-conditioned
path is the production path and is the tighter one. `docs/evidence/M8/README.md` and the risk
register both say so explicitly.

The report quotes **200.0 MiB against the 8 187.5 MiB device** as the operative ceiling, shows the
series so the reader can see how it was arrived at, and — following a rule this project has held
since M5 — **never describes any of these figures as comfortable headroom**.

## Gaps found, and what was done about them

Documentation corrections are permitted under the feature freeze
(`docs/process/feature-freeze.md`, "Allowed without a new decision"). Nothing under `apps/`, `ml/`,
`data/` or `outputs/` was touched.

| # | gap | disposition |
|---|---|---|
| G1 | **No bibliography anywhere.** The only external URLs in `docs/` are github.com, localhost, download.pytorch.org and huggingface.co | open — built in M9.8 from retrieved primary sources |
| G2 | **`docs/prototypes/prototype-3.md` did not exist** while 0, 1, 2, 4 and 5 did, and `docs/06-prototype-overview.md` promises every prototype gets one | **closed in M9.1** — written from EXP-016…EXP-019, DR-009 and `docs/evidence/prototype-3/` |
| G3 | **`docs/06-prototype-overview.md` listed Prototypes 3, 4 and 5 as "not started"** | **closed in M9.1** |
| G4 | **`README.md` suite counts stale** — 461 pytest / 169 vitest / 37 Playwright | **closed in M9.1** — 473 / 183 / 38 |
| G5 | **`README.md` project status stale** — "M8 in progress" | **closed in M9.1** |
| G6 | `docs/learning-outcome-traceability.md` header says "Last appended: M7" while M8 content is already in the cells | open — corrected when the M9 row is appended |
| G7 | `docs/09-final-reflection.md` is an empty skeleton | open — filled at the M9.10 human gate, not before |
| G8 | Planning v1 rows for M6/M7 still read "not started" | **not a gap** — v1 is never rewritten by rule; the change log carries the real course |
| G9 | `deliverables/` git-ignored while planning and issue #10 name it as the deliverable path | **closed in M9.2** — narrowest possible ignore exception |
| G10 | `deliverables/.gitkeep` tracked inside an ignored directory | **left alone** — harmless, already tracked, and out of M9's scope |
| G11 | M9 issue number and criteria unverified | **closed** — verified by Kylian, above |
| G12 | No `docs/evidence/M9/` | **closed in M9.1** — this file |

## Authoritative source per report chapter

| chapter feed | authoritative record |
|---|---|
| assignment, requirements, D1–D7 | `docs/00-project-brief.md`, Prompt 1 |
| research questions | `docs/01-research-plan.md` |
| planning and its changes | `docs/02-planning.md` — preserved v1 table + change log |
| architecture alternatives | `docs/03-architecture.md` (matrices D-A…D-F) |
| dataset | `data/manifests/dataset-v1.csv`, `docs/04-dataset-methodology.md`, DR-006 |
| methodology and rubric | `docs/05-experiment-methodology.md` |
| prototypes | `docs/prototypes/prototype-0…5.md` |
| experiments | `experiments/registry.csv` |
| decisions | `docs/decisions/DR-001…DR-015` |
| risks and limitations | `docs/process/risk-register.md`, `docs/process/feature-freeze.md` |
| testing | `docs/07-testing-strategy.md`, `docs/evidence/M8/baseline/`, `M8/tests/` |
| deployment | `docs/08-deployment-strategy.md`, DR-014, `docs/deployment/` |
| clean clone | `docs/evidence/M8/clean-clone/` |
| CI | `docs/evidence/M8/ci/`, `docs/evidence/M8/tests/ci-workflow.md` |
| AI usage | `docs/ai-usage.md` |
| chronology | `docs/process/process-log.md`, `git log` |

## Dataset composition, derived from the manifest

Computed from `data/manifests/dataset-v1.csv` during this audit, not quoted from prose.

| style | items | licence | source |
|---|---:|---|---|
| ukiyo-e | 55 | CC0 | Metropolitan Museum of Art, open access |
| minimal-geometric | 52 | project-original | `ml/dataset/generate_geometric.py`, seeded |
| retro-poster | 41 | public domain | Library of Congress (WPA / Federal Theatre Project) |
| **total** | **148** | | **splits:** 124 train · 17 val · 7 holdout |

## Experiment inventory

`experiments/registry.csv` holds **40 rows**: EXP-001…EXP-005, EXP-007…EXP-014 (with the 008b and
009b isolation checks), EXP-016…EXP-019 (with the a/b micro-gate variants), EXP-020…EXP-035 (with
EXP-024n12 and EXP-024n24).

**EXP-006 and EXP-015 are not experiment rows and their absence is not a gap** — those identifiers
belong to the scoring directories `docs/evidence/EXP-006-scoring/` and
`docs/evidence/EXP-015-scoring/`, which hold human rubric material rather than runs.

## Claims the report must not make

Collected here so the validator and the author work from one list. Each is a position an earlier
record took deliberately, and reversing it silently would be the failure this project has most
consistently avoided.

1. `retro-poster` is a **PARTIAL PASS**. Not a pass.
2. The byte-identical M8 reproduction is about **inference**. **R14 is about training.** Neither
   statement weakens the other.
3. ~200 MiB is **not** comfortable headroom.
4. The raised CI budgets are **not** a fix. The stall is real and unexplained, and a budget costs
   CI the ability to detect a genuine performance regression.
5. The CI green carries **three qualifications**: a green run also occurred under the old budgets;
   the per-scenario retry counts of the final green retry-enabled run are **unknown, not zero**;
   and a green under `retries: 2` with 180 s / 45 s CI budgets is **weaker** than a first-attempt
   green under 60 s / 10 s. The camera-preservation scenario's **first-attempt 40.2 s remote pass
   in run #7, before any budget rise**, stands without qualification.
6. DR-009 selects LoRA on **measured feasibility**, explicitly **not** on superiority — from-scratch
   training, full fine-tuning, DreamBooth and Textual Inversion were **screened, never run**.
7. RQ4's image-count result is **inconclusive**: non-monotonic, no minimum count established,
   **equal compute rather than equal epochs**, and measured on `minimal-geometric` only.
8. The generation total is **27**, never 25.
9. Zero dHash near-copy flags is a **coarse indicator**, not proof of no memorisation.
10. DR-007 rests on **two** measured base-model candidates; SD 2.1 was gated (HTTP 401).

## What this audit does not cover

It does not evaluate the report's writing, and it makes no research conclusion. Every RQ verdict,
every reflection judgement and the final conclusions remain Kylian's, taken at the M9.10 gate. This
file records only what evidence exists and which record governs where two disagree.

---

## Appended 2026-08-11 — corrections required at the M9.10 human gate

Three corrections were required by Kylian at the conclusions/reflection gate. All three are
recorded here because two of them corrected **claims this report had been making**, not merely
wording.

### 1. The AI-assistance disclosure overstated the human/AI separation

**The report claimed** that "every research conclusion, rubric score and production selection is the
student's" and that no score was generated by an assistant.

**The preserved evidence does not support that.** The Gate-1 scoring artifact's own header records
its reviewer line as **"ChatGPT visual review with Kylian present"**, and the Gate-2 artifact records
**"Final human approver: Kylian Algoet"** with **"Visual-analysis assistance: ChatGPT"**.
`docs/ai-usage.md` has said so since 2026-08-05.

**Corrected wording**, applied to the front matter, §3.1, §6.3, §6.4, §18.2.7, §19.2, §20.6, §25
Appendix D and §26.1:

> Visual evaluation was AI-assisted: ChatGPT contributed visual analysis and proposed scoring at the
> review gates, while Kylian Algoet reviewed and approved the recorded scores and retained final
> authority over every production selection and research conclusion.

Three things are preserved unchanged, because they remain true and are separately evidenced: the
**offline** indicators (perceptual hash, CLIP similarity) populated no rubric cell and selected no
checkpoint, weight, style or verdict; Kylian was the final human approver at both gates; and no
production or research decision was concluded solely by an assistant.

The limitation section was also corrected: it previously read "one scorer", which implied a single
unaided human rater. It now records **one human approver with AI-assisted visual analysis and no
second independent rater**, so no inter-rater agreement can be reported.

**No historical evidence file was edited.** The gate records and scoring artifacts are unchanged and
remain hash-locked.

### 2. The research-question status count was internally inconsistent

The report's prose said ten of twelve questions were answered while its own table showed four that
were not fully answered in their original wording. The taxonomy is now consistent throughout:

- **Answered within their stated scope (8):** RQ2, RQ3, RQ5, RQ6, RQ8, RQ9, RQ10, RQ12.
- **Bounded or partially answered (4):** RQ1, RQ4, RQ7, RQ11.
- **RQ4's image-count component remains explicitly INCONCLUSIVE.**

RQ1 moved from "answered" to **bounded** for a specific reason: the question asks which method is
*feasible and most effective*. Feasibility is demonstrated; **"most effective" was never
established**, because four of the five candidate methods were screened and never measured.

Corrected in §3.2, §5.2, §18.5, §19.2, §25 Appendix C and §26.3.

### 3. A generalisability overclaim

§19.3 introduced its findings with "Four results generalise past the assignment." That is stronger
than one GPU, one human approver and the documented validity threats support. It now reads that the
findings are **useful beyond this assignment as engineering lessons, without claiming statistical
generalisability**. The four findings and the section title are unchanged.

### What was NOT done

The 90-page length was **not** compressed further. Kylian accepted it at this gate on the basis that
no hard page limit exists in the assignment material, all 26 mandated sections are authored, and
evidence completeness takes precedence. The earlier compression pass had already removed genuine
repetition and moved the count by under one page, which identified the cause as structural: 26
mandated sections each beginning on a new page account for roughly 13 pages.

---

## Appended 2026-08-11 — M9.12 final gate and the submitted artifact

### The final wording correction

`No generation was ever run by an assistant` was replaced everywhere. It was more absolute than the
evidence supports, and ambiguous besides, because project commands were executed through the
development tooling environment. No evidence record states who physically launched each historical
generation, so the report no longer claims it. The established fact is stated instead:

> Every GPU generation was explicitly authorised by Kylian Algoet; no AI assistant had authority to
> initiate GPU inference without that approval.

`No assistant validated its own results` was likewise replaced, because it sat awkwardly beside the
corrected disclosure that visual evaluation **was** AI-assisted:

> No AI assistant had final validation or decision authority over its own work; AI-assisted visual
> evaluation was reviewed and approved by Kylian Algoet.

Corrected in the front matter, §6.4 (twice) and `docs/09-final-reflection.md`. Unchanged because
each is separately evidenced: the total is **27**, every generation required explicit authorisation,
the offline indicators populated no rubric cell and selected no checkpoint, and Kylian retained final
authority over production selections and research conclusions.

### A defect the rendered-page inspection caught, and the validator could not

**The bibliography printed `[1]` again at the start of each of its four subsections.** Reference 10
rendered as `[1]`, 12 as `[1]`, 15 as `[1]` — so the printed markers disagreed with the body, which
cites 1–20 continuously. The CSS counter was reset per list rather than per section.

**The validator was not wrong to miss it.** It checks the Markdown source, where the numbering was
correct throughout. The fault existed only in the presentation layer that replaced the list markers.
A source-level check cannot see a presentation-level defect — which is the argument for the visual
gate, restated as a finding rather than a principle.

### The submitted artifact

> **⚠️ SUPERSEDED on 2026-08-14 by M10.** The figures in this table were correct when M9 closed and
> are kept unchanged as the M9 record. They no longer identify the file on disk. Writing **DR-016**
> moved `decision_record_count` from 15 to 16, which added a row to Appendix B and rebuilt the report
> to **91 pages · 2 769 385 bytes ·
> `73f574158d83f7452a605d57b8c40541c45b2a0693fb69d66f280e9ea2677157`**. Current record:
> `docs/evidence/M10/build-record.md`.

| | |
|---|---|
| path | `deliverables/DeckForge-AI-research-report.pdf` |
| pages | **90** (heuristic: page-tree `/Count` agrees with the `/Type /Page` object count) |
| bytes | **2 756 980** |
| SHA-256 | `5c394e7a111374d3c1e7aa0d178db25144f22e1cc5736477b985095710ca8a93` |
| built from | `42b0ca9` |
| structural check | `%PDF-1.4` header, `%%EOF` trailer, non-empty |

**The SHA-256 identifies this artifact and makes no reproducibility claim.** The PDF is reproducible
in *content* from tracked sources; it is not byte-identical between builds, because Chrome embeds a
creation timestamp and its own version (DR-015).

### Final state at M9 closure

26 of 26 sections · all hard validator checks pass · 29 fact locks resolve · 20 references cited,
contiguous, no orphans · **489 pytest** · **no application, model or dataset file changed** ·
**generation total remains 27** · **no GPU inference occurred during M9**.
