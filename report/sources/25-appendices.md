# <span class="section-number">25</span> Appendices

## Appendix A — Experiment index

{{ facts.experiment_count }} rows in `experiments/registry.csv`. Each carries its research question,
hypothesis, dataset version, pinned model revision, full configuration, hardware readings, duration,
output paths, evaluation, conclusion, next action and commit.

| ID | proto | question | outcome |
|---|:---:|---|---|
| EXP-001 | 1 | Does PyTorch see CUDA on the audited GPU? | PASS — bf16 available as a documented fallback |
| EXP-002 | 1 | Is SD 1.5 feasible on 8 GB? | **Selected** — 2 675.38 MiB, 4.069 s |
| EXP-003 | 1 | Is SD 2.1 base feasible? | **BLOCKED** — HTTP 401 gating, nothing generated |
| EXP-004 | 1 | Is SDXL feasible at 512 and 1024? | **Rejected** — 10 738 MiB at 1024, silent host spill |
| EXP-005 | 1 | How should the deck aspect ratio be produced? | **Direct 1:3 selected**; hypothesis refuted |
| EXP-007 | 2 | Does IP-Adapter attach to the UNet, and at what cost? | PASS — 16 of 32 processors replaced, +1 248.69 MiB |
| EXP-008 | 2 | Is img2img influence controllable by strength? | Monotone, 6/6; **zero extra VRAM** |
| EXP-008b | 2 | Is the shared-process comparison valid for img2img? | PASS — +0.000 % against clean processes |
| EXP-009 | 2 | Is IP-Adapter influence controllable by scale? | Monotone, 6/6; **selected**, default 0.55 |
| EXP-009b | 2 | Is the shared-process comparison valid for IP-Adapter? | PASS — +0.000 % |
| EXP-010 | 2 | Does scale 0.0 reproduce the text-only baseline? | **12/12 byte-identical**; diagnostic, not a pass condition |
| EXP-011 | 2 | Which wins when prompt and reference conflict? | Prompt authority falls as influence rises; frame and pseudo-text transfer confirmed |
| EXP-012 | 2 | Does IP-Adapter-Plus do better? | **Not selected** — no decisive advantage, higher VRAM |
| EXP-013 | 2 | Does conditioning survive the deck format? | **All 6 near-copy flags are img2img here**; IP-Adapter memory-critical |
| EXP-014 | 2 | What do offline indicators say? | Monotone 6/6 both methods; 6 flags, all img2img |
| EXP-016a/b | 3 | Does one LoRA step run, and is the loop stable? | PASS — micro-gates before any longer run |
| EXP-016 | 3 | Does a LoRA train, save and reload? | PASS — 300 steps in 91 s |
| EXP-017a/b | 3 | Does training fit at the deck format? | PASS — feasibility probe only, 1 and 10 steps |
| EXP-018 | 3 | Does the adapter reload and change output? | PASS — 4/4 beyond a pre-declared noise floor |
| EXP-019a | 3 | Do LoRA and IP-Adapter coexist? | PASS — **first attempt preserved as a failed row** (runner defect) |
| EXP-019b | 3 | **R12:** does the combined stack fit the deck format? | **PASS by {{ facts.oneshot_spare_mib }} MiB** |
| EXP-020…022 | 4 | Do the three styles train with style-only captions? | PASS — pilots |
| EXP-023 | 4 | Do verbatim captions differ? | Blinded A/B; **style-only selected at Gate 1** |
| EXP-024n12/n24 | 4 | What is the effect of set size at equal compute? | **INCONCLUSIVE** — non-monotonic |
| EXP-025 | 4 | Which pilot checkpoint goes forward? | 108/108 generations at the cap |
| EXP-026 | 4 | Do the pilots reproduce training images? | 0 of 108 flagged |
| EXP-027 | 4 | Does the lead style reach a usable state? | **PASS — step 300 shipped** |
| EXP-028 | 4 | Does ukiyo-e? | **PASS — step 600 shipped** |
| EXP-029 | 4 | Does retro-poster, and does it bake in frames? | **PARTIAL PASS — step 300 shipped**; H4 confirmed |
| EXP-030 | 4 | One multi-style LoRA or separate adapters? | **Viable, not selected** |
| EXP-031 | 4 | How do the approved checkpoints behave across the matrix? | 252 of a 432 cap |
| EXP-032 | 4 | Does the trained stack still fit? | {{ facts.oneshot_spare_mib }} MiB for all four candidates; spill signature **absent** |
| EXP-033 | 4 | Do the approved checkpoints reproduce training images? | **0 of 252** flagged; coarse indicator only |
| EXP-034 | 5 | Does the stack survive as a long-lived service? | **Worst spare {{ facts.worst_spare_mib }} MiB**; growth 0.00 MiB |
| EXP-035 | 5 | Can the placeholder influence a prompt-only result? | Byte-identical at scale 0.0 — proven inert |

EXP-006 and EXP-015 are **not runs**: those identifiers name the human scoring directories.

## Appendix B — Decision records

{{ facts.decision_record_count }} records in `docs/decisions/`.

| DR | decision | notable for |
|---|---|---|
| DR-001 | Monorepo | one history as process evidence |
| DR-002 | FastAPI + Pydantic | validation weighted at 5 for untrusted uploads |
| DR-003 | React + Vite + TS + R3F | validated by Prototype 0 rather than argued |
| DR-004 | Diffusers + PEFT + Accelerate | kohya fallback retired only after measurement |
| DR-005 | Procedural deck geometry | removed model licensing entirely |
| DR-006 | Three styles and their sources | graffiti replaced by ukiyo-e on licensing risk |
| DR-007 | SD 1.5, direct 1:3 at 512×1536 | rests on **two** measured candidates |
| DR-008 | Standard IP-Adapter @ 0.55 | img2img retained as a labelled fallback |
| DR-009 | LoRA, rank {{ facts.lora_rank }} | **claims feasibility, not superiority** |
| DR-010 | Three per-style adapters @ {{ facts.lora_weight_default }} | two of three ship at step 300 |
| DR-011 | Single-process resident service | a memory measurement, not a preference |
| DR-012 | `full-surface` texture fit | student's rationale quoted **verbatim** |
| DR-013 | Real progress telemetry | no percentage without a denominator |
| DR-014 | Native local deployment | Docker **screened out, not benchmarked** |
| DR-015 | Report build pipeline | zero new dependencies under the freeze |
| DR-016 | Presentation build pipeline | extends DR-015; the deck inherits the report's fact locks |
| DR-017 | Deck length for a 20-minute slot | a constraint absent from the repository could not be checked |

## Appendix C — Research-question matrix

**Eight of twelve answered within their stated scope: RQ2, RQ3, RQ5, RQ6, RQ8, RQ9, RQ10, RQ12.
Four bounded or partially answered: RQ1, RQ4, RQ7, RQ11.** RQ4's image-count component is explicitly
**inconclusive**.

The full statement of each question is in §5.2, the status table in §26.3, and the conclusions drawn
in §19.2.

## Appendix D — Risk register summary

| ID | risk | status |
|---|---|---|
| R1 | 8 GB insufficient for the chosen configuration | mitigating — quantified both sides |
| R3 | Dataset licensing gaps | open — policy enforced pre-collection |
| R5 | Windows CUDA/tooling friction | **closed** — occurred, resolved, pins recorded |
| R8 | Style-learning quality plateau | open — one partial pass |
| R9 | Evaluation subjectivity | open — AI-assisted analysis, one human approver, no second rater |
| R10 | 3D model licensing | **closed** — procedural geometry |
| R11 | Third-party hosting unavailable | **occurred four times** (§12.1, §24.4) |
| R12 | Combined stack does not fit | **re-scoped, not closed** — fits by {{ facts.worst_spare_mib }} MiB |
| R13 | Reference conditioning reproduces the reference | **occurred**, mitigated by method selection |
| R14 | **Training not bit-reproducible from seed** | **occurred** — bounded, permanent |
| R15 | Live demonstration fails on stage | mitigating — four-rung fallback |
| R16 | Production checkpoints cannot be restored | mitigating — **external backup not exercised** |

## Appendix E — Fact locks

Every quantitative value repeated in this report is substituted at build time from
`report/facts.yaml` and proved against the evidence file that states it. Extraction is graded:
structural parsing for CSV and JSON, full 64-character matching for hashes, and context-anchored
patterns for prose that must match exactly once — an ambiguous anchor is treated as a broken one,
because it could confirm a superseded value as readily as the current one.

Sixteen tests assert this, six of them negative cases that prove the guards reject a wrong value, a
stale value taken from the wrong column of the right table, an ambiguous anchor, a truncated hash, a
missing source and a dead anchor.

## Appendix F — Reproducing this document

```
python scripts/build_report.py        # sources -> HTML -> PDF
python scripts/validate_report.py     # structure, references, identifiers, facts
```

Chrome is a build prerequisite (DR-015). The PDF is reproducible in **content** from tracked sources;
it is **not** byte-identical between builds, because Chrome embeds a creation timestamp and its own
version. The recorded SHA-256 identifies the submitted artifact and makes no reproducibility claim
beyond that.
