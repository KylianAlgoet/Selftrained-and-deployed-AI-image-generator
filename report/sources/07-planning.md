# <span class="section-number">7</span> Planning, original and changed

## 7.1 The original plan

Twelve milestones (M0–M11) were planned on 2026-07-27, the first day, covering roughly 132 focused
hours across 21 days. The plan is published as a public GitHub Project mirroring each milestone as a
repository issue with objective, acceptance criteria, dates, dependencies and expected evidence —
satisfying the assignment's public-planning requirement.

**One rule governs the planning document: the original plan is never rewritten.** Adjustments are
appended to a change log with their reasons. A plan that is edited to match what happened is not
evidence of planning; it is evidence of hindsight. This means the v1 table still shows later
milestones as *not started* even though they are complete, and that apparent staleness is the
convention working as intended.

| M | milestone | planned | actual | estimate → actual |
|---|---|---|---|---|
| M0 | Phase 0 foundation | Jul 27–28 | Jul 27 | 6 h |
| M1 | Prototype 0 — 3D viewer | Jul 28–30 | **Jul 27** | 10 h → ~4 h |
| M2 | Dataset research and pipeline | Jul 30 – Aug 3 | **Jul 27** | 16 h → ~5 h |
| M3 | Prototype 1 — base-model benchmark | Aug 2–4 | **Jul 30** | 10 h → ~8 h |
| M4 | Prototype 2 — reference conditioning | Aug 4–6 | **Aug 1** | 10 h → ~9 h |
| M5 | Prototype 3 — LoRA smoke test | Aug 6–8 | **Aug 4** | 10 h → ~5 h |
| M6 | Prototype 4 — style learning | Aug 8–11 | **Aug 5** | 14 h → ~10 h |
| M7 | Prototype 5 — integrated MVP | Aug 10–13 | **Aug 7** | 18 h → ~13 h |
| M8 | Testing, deployment, demo | Aug 13–15 | **Aug 9** | 10 h → ~11 h |

Every milestone but one came in early, and the buffer compounded: M1 and M2 finishing on day one
bought roughly two days, which let the benchmark start early, which let conditioning start early, and
so on. **M8 is the only milestone that overran its estimate**, by about an hour, and §7.3 explains
why that overrun was worth more than the savings.

## 7.2 Why the under-runs happened

The under-runs are recorded with measured causes rather than attributed to good luck, because two of
them changed later estimates.

**Infrastructure was reusable to a degree the estimates did not anticipate.** The MVP milestone
added no modelling of its own: it reuses the conditioning attachment with its pinned-encoder
workaround, the frozen prompt kit and the adapter-scale mechanism unchanged, which is also why its
memory behaviour is directly comparable with the experiments that preceded it.

**Training was far cheaper than budgeted.** Three hundred steps cost 91 seconds. The "long training
run" the 10-hour estimate assumed never existed, and the entire memory-escalation contingency went
unused because nothing ever escalated past the lowest tier.

**A procedural decision removed a whole work package.** Generating the deck geometry procedurally
rather than sourcing a model eliminated model licensing, UV repair and import work from the first
milestone.

## 7.3 The change log

Thirteen entries record every adjustment with its reason and its impact. Six matter to the research
narrative.

**The style set changed before collection.** The planned graffiti/street-art style was replaced with
ukiyo-e woodblock because graffiti photography is generally artist-copyrighted while ukiyo-e has
large institutional public-domain supply. A licensing risk was designed out rather than mitigated
later (§17).

**A style was relabelled before any experiment ran.** `retro-comic` became `retro-poster` after the
student's own pre-check found the label contradicted the collected material: it is silkscreen poster
work with no halftone, panels or sequential art. The wrong label had already reached the draft prompt
kit, and every later style comparison would have been built on it. Correcting it cost about an hour;
finding it later would have invalidated the comparisons.

**Two dataset sources became unavailable mid-collection** and the shares were shifted to
already-approved alternatives rather than by adding new sources (§12.1).

**A review gate was split in two after the student's plan review.** The style-learning plan
originally promised a review gate and then authorised the full runs and the final matrix before
anything had been seen. The split into pilots → gate → approved runs → gate is what made the first
gate a decision point rather than a formality, and it produced three further corrections including
the equal-compute image-count arm.

**Scope was added twice, deliberately and recorded.** Real generation progress and local decal upload
were both scoped by the student after using the application, neither was in the plan, and both are
logged with their reasons. The progress work produced a decision record and found three defects no
test could see.

**A generation budget was exceeded, and recorded rather than absorbed.** The research cap of 25 was
reached exactly. Generation 26 was the student's own review run and 27 was deployment validation;
neither carries an experiment identifier and neither is in the registry, because adding them would
contaminate a frozen matrix. The total is reported as **{{ facts.generations_total }}**.

## 7.4 The feature freeze

The plan set the freeze at 2026-08-15. It was brought forward to **2026-08-09**, the day the
implementation work actually finished, on the reasoning that a freeze starting when the work is done
is worth more than one starting on a calendar date, and that the remaining risk was no longer "does
it work" but "does a late change break something that was working".

The freeze permits blocking bug fixes, documentation, test fixes, demo preparation and evidence
organisation. It forbids retraining, new styles, architecture changes, UI redesign, new generation
features, model replacement, geometry changes and dependency upgrades without a new decision record.
This report was written under it, and the only decision record it required is DR-015, for the build
that produced this PDF.

The freeze also fixes what "done" means: it lists **eight accepted limitations** and states that they
are limitations rather than unfinished work (§18). That distinction was made at a review gate, before
this report existed, so it could not be made retroactively to suit the writing.
